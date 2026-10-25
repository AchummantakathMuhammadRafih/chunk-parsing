"""Click CLI commands for MinerU PDF conversion."""

import os
import sys
from pathlib import Path
from typing import Optional
import click

from mineru_converter.config.constants import (
    DEFAULT_DOCLING_MAX_TOKENS,
    DEFAULT_DOCLING_TOKENIZER,
    DEFAULT_DOCLING_URL,
    DEFAULT_OUTPUT_DIR,
    SUPPORTED_LANGUAGES,
    BackendType,
    HybridEffort,
    ParseMethod,
)
from mineru_converter.config.settings import ConversionConfig
from mineru_converter.core.converter import MinerUConverter
from mineru_converter.exporters.manifest import build_output_manifest, calculate_document_stats
from mineru_converter.cli.formatters import (
    print_banner,
    print_batch_summary,
    print_conversion_result,
)
from mineru_converter.utils.file_utils import find_input_files, format_file_size
from mineru_converter.utils.logging_utils import console, setup_logger


def docling_options(func):
    """Shared Docling chunking options for convert and batch."""
    options = [
        click.option("--no-docling", is_flag=True, default=False, help="Skip Docling hybrid chunking of the Markdown."),
        click.option("--docling-url", type=str, default=DEFAULT_DOCLING_URL, show_default=True, help="docling-serve base URL."),
        click.option("--docling-max-tokens", type=click.IntRange(min=1), default=DEFAULT_DOCLING_MAX_TOKENS, show_default=True, help="Max tokens per chunk."),
        click.option("--docling-tokenizer", type=str, default=DEFAULT_DOCLING_TOKENIZER, show_default=True, help="HuggingFace tokenizer for the hybrid chunker."),
        click.option("--docling-timeout", type=click.IntRange(min=1), default=300, show_default=True, help="docling-serve request timeout (s)."),
    ]
    for option in reversed(options):
        func = option(func)
    return func


@click.group(invoke_without_command=False)
@click.version_option(version="1.0.0", prog_name="mineru-converter")
def cli():
    """MinerU PDF Converter - High-fidelity PDF to Markdown, JSON, and Media toolkit."""
    pass


@cli.command("convert")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o", "--output", "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Target directory for output artifacts."
)
@click.option(
    "-b", "--backend",
    type=click.Choice([b.value for b in BackendType]),
    default=BackendType.PIPELINE.value,
    show_default=True,
    help="MinerU backend parser engine."
)
@click.option(
    "-m", "--method",
    type=click.Choice([m.value for m in ParseMethod]),
    default=ParseMethod.AUTO.value,
    show_default=True,
    help="Parsing mode (auto, txt for fast text extraction, ocr for scans)."
)
@click.option(
    "-l", "--lang",
    type=str,
    default="ch",
    show_default=True,
    help=f"Language code for OCR (e.g. {', '.join(SUPPORTED_LANGUAGES[:6])}, en)."
)
@click.option(
    "--effort",
    type=click.Choice([e.value for e in HybridEffort]),
    default=HybridEffort.MEDIUM.value,
    show_default=True,
    help="Effort level for hybrid backend (medium or high)."
)
@click.option("-s", "--start-page", type=int, default=0, show_default=True, help="Start page index (0-indexed).")
@click.option("-e", "--end-page", type=int, default=None, help="End page index (0-indexed, inclusive).")
@click.option("--no-formula", is_flag=True, default=False, help="Disable formula/LaTeX extraction.")
@click.option("--no-table", is_flag=True, default=False, help="Disable table structure recognition.")
@click.option("--no-images", is_flag=True, default=False, help="Skip saving extracted images to disk under images/ folder.")
@click.option("--no-layout-pdf", is_flag=True, default=False, help="Skip generating annotated layout PDF.")
@click.option("--no-span-pdf", is_flag=True, default=False, help="Skip generating annotated span PDF.")
@click.option("--no-manifest", is_flag=True, default=False, help="Skip writing manifest/summary JSON files.")
@click.option("--capture-header/--no-capture-header", default=True, show_default=True, help="Elevate first heading to top level (#) if needed.")
@click.option("-u", "--server-url", type=str, default=None, help="URL for remote VLM/hybrid server.")
@docling_options
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose debug logging.")
@click.option("-q", "--quiet", is_flag=True, default=False, help="Suppress informational messages.")
def convert_cmd(
    input_path: Path,
    output_dir: Path,
    backend: str,
    method: str,
    lang: str,
    effort: str,
    start_page: int,
    end_page: Optional[int],
    no_formula: bool,
    no_table: bool,
    no_images: bool,
    no_layout_pdf: bool,
    no_span_pdf: bool,
    no_manifest: bool,
    capture_header: bool,
    server_url: Optional[str],
    no_docling: bool,
    docling_url: str,
    docling_max_tokens: Optional[int],
    docling_tokenizer: Optional[str],
    docling_timeout: int,
    verbose: bool,
    quiet: bool,
):
    """Convert a single PDF file into Markdown, V1/V2 Content Lists, Middle AST, Model JSON, Visual PDFs, and extracted images."""
    if not quiet:
        print_banner()

    setup_logger(verbose=verbose, quiet=quiet)

    config = ConversionConfig(
        output_dir=output_dir,
        backend=BackendType(backend),
        method=ParseMethod(method),
        lang=lang,
        effort=HybridEffort(effort),
        start_page=start_page,
        end_page=end_page,
        formula_enable=not no_formula,
        table_enable=not no_table,
        dump_images=not no_images,
        draw_layout_bbox=not no_layout_pdf,
        draw_span_bbox=not no_span_pdf,
        generate_manifest=not no_manifest,
        capture_header=capture_header,
        server_url=server_url,
        docling_enable=not no_docling,
        docling_url=docling_url,
        docling_max_tokens=docling_max_tokens,
        docling_tokenizer=docling_tokenizer,
        docling_timeout=docling_timeout,
    )

    converter = MinerUConverter(config=config)
    result = converter.convert(input_path)

    if not quiet:
        print_conversion_result(result)

    if not result.success:
        sys.exit(1)


@cli.command("batch")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o", "--output", "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Target directory for output artifacts."
)
@click.option("-r", "--recursive/--no-recursive", default=True, show_default=True, help="Search directory recursively.")
@click.option(
    "-b", "--backend",
    type=click.Choice([b.value for b in BackendType]),
    default=BackendType.PIPELINE.value,
    show_default=True,
    help="MinerU backend parser engine."
)
@click.option(
    "-m", "--method",
    type=click.Choice([m.value for m in ParseMethod]),
    default=ParseMethod.AUTO.value,
    show_default=True,
    help="Parsing mode (auto, txt, ocr)."
)
@click.option("-l", "--lang", type=str, default="ch", show_default=True, help="Language code for OCR.")
@click.option("--no-images", is_flag=True, default=False, help="Skip saving extracted images to disk under images/ folder.")
@click.option("--capture-header/--no-capture-header", default=True, show_default=True, help="Elevate first heading to top level (#) if needed.")
@click.option("--stop-on-error", is_flag=True, default=False, help="Halt batch conversion on first error.")
@docling_options
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose debug logging.")
@click.option("-q", "--quiet", is_flag=True, default=False, help="Suppress informational messages.")
def batch_cmd(
    input_dir: Path,
    output_dir: Path,
    recursive: bool,
    backend: str,
    method: str,
    lang: str,
    no_images: bool,
    capture_header: bool,
    stop_on_error: bool,
    no_docling: bool,
    docling_url: str,
    docling_max_tokens: Optional[int],
    docling_tokenizer: Optional[str],
    docling_timeout: int,
    verbose: bool,
    quiet: bool,
):
    """Batch convert all PDF files within a directory."""
    if not quiet:
        print_banner()

    setup_logger(verbose=verbose, quiet=quiet)

    # Discover files
    try:
        files = find_input_files(input_dir, recursive=recursive, only_pdf=True)
    except Exception as exc:
        console.print(f"[bold red]Error discovering files:[/bold red] {exc}")
        sys.exit(1)

    if not files:
        console.print(f"[bold yellow]No PDF files found in:[/bold yellow] {input_dir}")
        return

    console.print(f"Found [bold cyan]{len(files)}[/bold cyan] PDF documents to convert.")

    config = ConversionConfig(
        output_dir=output_dir,
        backend=BackendType(backend),
        method=ParseMethod(method),
        lang=lang,
        dump_images=not no_images,
        capture_header=capture_header,
        docling_enable=not no_docling,
        docling_url=docling_url,
        docling_max_tokens=docling_max_tokens,
        docling_tokenizer=docling_tokenizer,
        docling_timeout=docling_timeout,
    )

    converter = MinerUConverter(config=config)
    summary = converter.convert_batch(files, stop_on_error=stop_on_error)

    if not quiet:
        print_batch_summary(summary)

    if summary.failed_count > 0:
        sys.exit(1)


@cli.command("inspect")
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def inspect_cmd(target_dir: Path):
    """Inspect and display generated MinerU artifacts and statistics in a directory."""
    print_banner()

    doc_stem = target_dir.name
    # Handle if pointing to method subfolder
    if target_dir.name in ("auto", "txt", "ocr", "vlm", "hybrid", "pipeline"):
        doc_stem = target_dir.parent.name

    manifest = build_output_manifest(target_dir, doc_stem=doc_stem)

    if not any(manifest.all_files()):
        console.print(f"[bold red]No MinerU output artifacts found in:[/bold red] {target_dir}")
        return

    stats = calculate_document_stats(
        manifest=manifest,
        input_file=Path(doc_stem + ".pdf"),
        total_pages=0,
        processed_pages=0,
        duration_seconds=0.0
    )

    from mineru_converter.models.schemas import ConversionResult
    dummy_result = ConversionResult(
        success=True,
        input_path=Path(doc_stem + ".pdf"),
        document_name=doc_stem,
        manifest=manifest,
        stats=stats,
    )
    print_conversion_result(dummy_result)


@cli.command("chunk")
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output", "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Optional output directory for docling_chunks.json. Defaults to the same directory as the target."
)
@click.option("--docling-url", type=str, default=DEFAULT_DOCLING_URL, show_default=True, help="docling-serve base URL.")
@click.option("--docling-max-tokens", type=click.IntRange(min=1), default=DEFAULT_DOCLING_MAX_TOKENS, show_default=True, help="Max tokens per chunk.")
@click.option("--docling-tokenizer", type=str, default=DEFAULT_DOCLING_TOKENIZER, show_default=True, help="HuggingFace tokenizer for the hybrid chunker.")
@click.option("--docling-timeout", type=click.IntRange(min=1), default=300, show_default=True, help="docling-serve request timeout (s).")
def chunk_cmd(
    target: Path,
    output_dir: Optional[Path],
    docling_url: str,
    docling_max_tokens: int,
    docling_tokenizer: str,
    docling_timeout: int,
):
    """Run Docling hybrid chunking directly on an existing Markdown file or MinerU output directory."""
    print_banner()

    from mineru_converter.exporters.docling_chunks import run_docling_chunking
    from mineru_converter.models.schemas import OutputFileManifest

    if target.is_file():
        if target.suffix.lower() != ".md":
            console.print(f"[bold red]Target file must be a Markdown (.md) file:[/bold red] {target}")
            sys.exit(1)
        markdown_path = target
        working_dir = target.parent
        doc_stem = target.stem
    else:
        working_dir = target
        doc_stem = target.name
        if doc_stem in ("auto", "txt", "ocr", "vlm", "hybrid", "pipeline"):
            doc_stem = target.parent.name
        markdown_path = working_dir / f"{doc_stem}.md"
        if not markdown_path.exists():
            # Search for any .md file in the directory
            md_files = list(working_dir.glob("*.md"))
            if md_files:
                markdown_path = md_files[0]
                doc_stem = markdown_path.stem
            else:
                console.print(f"[bold red]No Markdown (.md) file found in:[/bold red] {working_dir}")
                sys.exit(1)

    content_list_path = working_dir / f"{doc_stem}_content_list.json"
    if not content_list_path.exists():
        cl_files = list(working_dir.glob("*_content_list.json"))
        if cl_files:
            content_list_path = cl_files[0]

    dest_dir = output_dir or working_dir

    manifest = OutputFileManifest(
        document_name=doc_stem,
        output_directory=dest_dir,
        markdown_path=markdown_path,
        content_list_v1_path=content_list_path if content_list_path.exists() else None,
    )

    config = ConversionConfig(
        docling_url=docling_url,
        docling_max_tokens=docling_max_tokens,
        docling_tokenizer=docling_tokenizer,
        docling_timeout=docling_timeout,
    )

    console.print(f"[bold cyan]Document:[/bold cyan] {doc_stem}")
    console.print(f"[bold cyan]Markdown:[/bold cyan] {markdown_path}")
    console.print(f"[bold cyan]Content List:[/bold cyan] {content_list_path if content_list_path.exists() else 'Not found (images will be skipped)'}")
    console.print(f"[bold cyan]Output Directory:[/bold cyan] {dest_dir}\n")

    with console.status("[bold green]Running Docling hybrid chunking & image linking..."):
        try:
            out_file, chunk_count, attached_count = run_docling_chunking(manifest, config)
        except Exception as e:
            console.print(f"[bold red]Chunking failed:[/bold red] {e}")
            sys.exit(1)

    console.print(f"[bold green]✓ Successfully generated:[/bold green] {out_file}")
    console.print(f"[bold cyan]* Total Chunks:[/bold cyan] {chunk_count}")
    console.print(f"[bold cyan]* Total Images Attached:[/bold cyan] {attached_count}")


@cli.command("info")
def info_cmd():
    """Display environment, MinerU version, GPU/device status, and cached model paths."""
    print_banner()
    import torch
    import mineru

    console.print("[bold cyan]System & MinerU Environment Information:[/bold cyan]")
    console.print(f"* [bold]MinerU Version:[/bold] {mineru.__version__ if hasattr(mineru, '__version__') else 'Installed'}")
    console.print(f"* [bold]Python Executable:[/bold] {sys.executable}")
    console.print(f"* [bold]PyTorch Version:[/bold] {torch.__version__}")
    console.print(f"* [bold]CUDA Available:[/bold] {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        console.print(f"* [bold]GPU Device:[/bold] {torch.cuda.get_device_name(0)}")
        console.print(f"* [bold]Device Count:[/bold] {torch.cuda.device_count()}")
    else:
        console.print("* [bold]Compute Mode:[/bold] CPU")

    home = Path.home()
    console.print(f"* [bold]User Home:[/bold] {home}")
    mineru_json = home / "mineru.json"
    console.print(f"* [bold]mineru.json Config:[/bold] {'[green]Exists[/green]' if mineru_json.exists() else '[yellow]Not Found[/yellow]'}")
    hf_cache = home / ".cache" / "huggingface" / "hub"
    console.print(f"* [bold]HuggingFace Cache:[/bold] {hf_cache} ({'[green]Found[/green]' if hf_cache.exists() else '[yellow]Not Found[/yellow]'})")
