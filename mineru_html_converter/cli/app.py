"""Click command line interface for MinerU HTML Converter."""

import sys
from pathlib import Path
from typing import Optional
import click

from mineru_html_converter.config.constants import (
    DEFAULT_OUTPUT_DIR,
    RenderModeEnum,
    ThemeEnum,
)
from mineru_html_converter.config.settings import HTMLConversionConfig
from mineru_html_converter.core.converter import MinerUHTMLConverter
from mineru_html_converter.cli.formatters import print_banner, print_conversion_result
from mineru_html_converter.utils.file_utils import find_supported_documents
from mineru_html_converter.utils.logging_utils import console, setup_logger


@click.group(invoke_without_command=False)
@click.version_option(version="1.1.0", prog_name="mineru-html")
def cli():
    """MinerU Document to HTML Converter - High-fidelity HTML toolkit for PDF, DOCX, PPTX, XLSX."""
    pass


@cli.command("convert")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output", "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Target HTML output file path or directory. Defaults to output/html/<filename>.html."
)
@click.option(
    "-p", "--pages",
    type=str,
    default=None,
    help="Page range to convert (e.g., '1-5,8', '1-10'). Default: all pages."
)
@click.option(
    "-m", "--mode",
    type=click.Choice([m.value for m in RenderModeEnum]),
    default=RenderModeEnum.DEFAULT.value,
    show_default=True,
    help="Render mode: 'default' (responsive article) or 'full' (page-based containers)."
)
@click.option(
    "-t", "--theme",
    type=click.Choice([t.value for t in ThemeEnum]),
    default=ThemeEnum.MODERN.value,
    show_default=True,
    help="Visual theme: modern, dark, readable, minimal."
)
@click.option(
    "--embed-images/--no-embed-images",
    default=True,
    show_default=True,
    help="Inline extracted images as base64 data URIs into the HTML file."
)
@click.option(
    "--toc/--no-toc",
    default=True,
    show_default=True,
    help="Inject an interactive floating Table of Contents sidebar."
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Custom document title for the HTML header."
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable detailed debug logging."
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    default=False,
    help="Suppress banners and summary output."
)
def convert_cmd(
    input_path: Path,
    output_path: Optional[Path],
    pages: Optional[str],
    mode: str,
    theme: str,
    embed_images: bool,
    toc: bool,
    title: Optional[str],
    verbose: bool,
    quiet: bool,
):
    """Convert a PDF document into high-fidelity HTML."""
    setup_logger(verbose=verbose)
    if not quiet:
        print_banner()

    # Determine output target
    out_dir = DEFAULT_OUTPUT_DIR
    out_file = None

    if output_path:
        if output_path.suffix.lower() == ".html":
            out_file = output_path
            out_dir = output_path.parent
        else:
            out_dir = output_path

    config = HTMLConversionConfig(
        output_dir=out_dir,
        pages=pages,
        mode=RenderModeEnum(mode),
        theme=ThemeEnum(theme),
        embed_images=embed_images,
        add_toc=toc,
        document_title=title,
    )

    converter = MinerUHTMLConverter(config=config)
    result = converter.convert(input_path=input_path, output_path=out_file)

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
    help="Directory where converted HTML files will be saved."
)
@click.option(
    "-p", "--pages",
    type=str,
    default=None,
    help="Page range to convert for each PDF (e.g. '1-3')."
)
@click.option(
    "-m", "--mode",
    type=click.Choice([m.value for m in RenderModeEnum]),
    default=RenderModeEnum.DEFAULT.value,
    show_default=True,
    help="Render mode."
)
@click.option(
    "-t", "--theme",
    type=click.Choice([t.value for t in ThemeEnum]),
    default=ThemeEnum.MODERN.value,
    show_default=True,
    help="Visual theme."
)
@click.option(
    "--embed-images/--no-embed-images",
    default=True,
    show_default=True,
    help="Inline images as base64."
)
@click.option(
    "--toc/--no-toc",
    default=True,
    show_default=True,
    help="Inject floating Table of Contents."
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose debug logging."
)
def batch_cmd(
    input_dir: Path,
    output_dir: Path,
    pages: Optional[str],
    mode: str,
    theme: str,
    embed_images: bool,
    toc: bool,
    verbose: bool,
):
    """Batch convert all supported documents (PDF, DOCX, PPTX, XLSX) in a directory to HTML."""
    setup_logger(verbose=verbose)
    print_banner()

    doc_files = find_supported_documents(input_dir)
    if not doc_files:
        console.print(f"[yellow]No supported document files found in {input_dir}[/yellow]")
        return

    console.print(f"[bold cyan]Found {len(doc_files)} documents to convert.[/bold cyan]\n")

    config = HTMLConversionConfig(
        output_dir=output_dir,
        pages=pages,
        mode=RenderModeEnum(mode),
        theme=ThemeEnum(theme),
        embed_images=embed_images,
        add_toc=toc,
    )
    converter = MinerUHTMLConverter(config=config)

    success_count = 0
    fail_count = 0

    for doc_file in doc_files:
        console.print(f"Processing: [cyan]{doc_file.name}[/cyan] ...")
        res = converter.convert(doc_file)
        if res.success:
            success_count += 1
            console.print(f" -> [green]Done:[/green] {res.output_html_file.name} ({res.duration_seconds}s)")
        else:
            fail_count += 1
            console.print(f" -> [red]Failed:[/red] {res.error_message}")

    console.print(f"\n[bold]Batch Completed:[/bold] [green]{success_count} succeeded[/green], [red]{fail_count} failed[/red].")
