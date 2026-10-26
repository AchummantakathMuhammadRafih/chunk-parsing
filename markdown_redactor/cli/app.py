"""Click command line interface for Markdown PII Redactor."""

import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.table import Table

from markdown_redactor.config.constants import (
    DEFAULT_ENTITIES,
    DEFAULT_MASK_CHAR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCORE_THRESHOLD,
)
from markdown_redactor.config.settings import RedactionConfig
from markdown_redactor.core.redactor import MarkdownRedactor
from markdown_redactor.cli.formatters import print_banner, print_redaction_result
from markdown_redactor.utils.file_utils import find_markdown_files
from markdown_redactor.utils.logging_utils import console, setup_logger


@click.group(invoke_without_command=False)
@click.version_option(version="1.0.0", prog_name="markdown-redact")
def cli():
    """Markdown PII Redactor - Anonymize PII in markdown files with star-masking using Microsoft Presidio."""
    pass


@cli.command("redact")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output", "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Target redacted file path or directory. Default: appends .redacted.md"
)
@click.option(
    "-t", "--threshold",
    type=float,
    default=DEFAULT_SCORE_THRESHOLD,
    show_default=True,
    help="Presidio detection confidence threshold (0.0 - 1.0)."
)
@click.option(
    "-e", "--entity", "entities",
    multiple=True,
    type=str,
    default=None,
    help="Specific entity type to redact (e.g. -e PERSON -e EMAIL_ADDRESS). Can be passed multiple times."
)
@click.option(
    "-m", "--mask-char",
    type=str,
    default=DEFAULT_MASK_CHAR,
    show_default=True,
    help="Masking character (e.g., '*')."
)
@click.option(
    "--keep-code/--redact-code",
    default=True,
    show_default=True,
    help="Preserve markdown code blocks and inline code untouched."
)
@click.option(
    "--keep-images/--redact-images",
    default=True,
    show_default=True,
    help="Preserve markdown image target URLs untouched."
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
def redact_cmd(
    input_path: Path,
    output_path: Optional[Path],
    threshold: float,
    entities: Optional[tuple],
    mask_char: str,
    keep_code: bool,
    keep_images: bool,
    verbose: bool,
    quiet: bool,
):
    """Redact PII from a single markdown file."""
    setup_logger(verbose=verbose)
    if not quiet:
        print_banner()

    active_entities = list(entities) if entities else list(DEFAULT_ENTITIES)

    config = RedactionConfig(
        entities=active_entities,
        score_threshold=threshold,
        mask_char=mask_char,
        ignore_code_blocks=keep_code,
        ignore_image_urls=keep_images,
    )

    redactor = MarkdownRedactor(config=config)

    # Determine destination
    target_out: Optional[Path] = None
    if output_path:
        if output_path.is_dir() or output_path.suffix == "":
            target_out = output_path / f"{input_path.stem}.redacted{input_path.suffix}"
        else:
            target_out = output_path

    with console.status("[bold cyan]Scanning and redacting Markdown file...[/bold cyan]"):
        result = redactor.redact_file(input_file=input_path, output_file=target_out)

    if not quiet:
        print_redaction_result(result)

    if not result.success:
        sys.exit(1)


@cli.command("batch")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o", "--output-dir", "output_dir",
    type=click.Path(path_type=Path),
    default=Path(DEFAULT_OUTPUT_DIR),
    show_default=True,
    help="Destination directory for redacted files."
)
@click.option(
    "-t", "--threshold",
    type=float,
    default=DEFAULT_SCORE_THRESHOLD,
    show_default=True,
    help="Presidio detection confidence threshold (0.0 - 1.0)."
)
@click.option(
    "-e", "--entity", "entities",
    multiple=True,
    type=str,
    default=None,
    help="Specific entity type to redact."
)
@click.option(
    "-m", "--mask-char",
    type=str,
    default=DEFAULT_MASK_CHAR,
    show_default=True,
    help="Masking character."
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    show_default=True,
    help="Scan directory recursively."
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
    help="Suppress banners."
)
def batch_cmd(
    input_dir: Path,
    output_dir: Path,
    threshold: float,
    entities: Optional[tuple],
    mask_char: str,
    recursive: bool,
    verbose: bool,
    quiet: bool,
):
    """Batch redact all markdown files within a directory."""
    setup_logger(verbose=verbose)
    if not quiet:
        print_banner()

    md_files = find_markdown_files(input_dir, recursive=recursive)
    if not md_files:
        console.print(f"[bold yellow]No markdown files (.md, .markdown) found in:[/bold yellow] {input_dir}")
        return

    console.print(f"[bold cyan]Found {len(md_files)} markdown files in {input_dir}[/bold cyan]")
    output_dir.mkdir(parents=True, exist_ok=True)

    active_entities = list(entities) if entities else list(DEFAULT_ENTITIES)
    config = RedactionConfig(
        entities=active_entities,
        score_threshold=threshold,
        mask_char=mask_char,
    )
    redactor = MarkdownRedactor(config=config)

    total_findings = 0
    success_count = 0
    failure_count = 0

    batch_table = Table(title="[bold green]Batch Redaction Summary[/bold green]", show_header=True)
    batch_table.add_column("File", style="cyan")
    batch_table.add_column("Findings", justify="right")
    batch_table.add_column("Time", justify="right")
    batch_table.add_column("Status", justify="center")

    with console.status("[bold cyan]Processing markdown files...[/bold cyan]"):
        for md_file in md_files:
            rel_path = md_file.relative_to(input_dir) if md_file.is_relative_to(input_dir) else md_file.name
            out_file = output_dir / rel_path

            res = redactor.redact_file(input_file=md_file, output_file=out_file)
            if res.success:
                success_count += 1
                total_findings += res.findings_count
                batch_table.add_row(str(rel_path), str(res.findings_count), f"{res.execution_time:.2f}s", "[green]✔ Success[/green]")
            else:
                failure_count += 1
                batch_table.add_row(str(rel_path), "0", f"{res.execution_time:.2f}s", f"[red]✘ {res.error_message}[/red]")

    console.print(batch_table)
    console.print(f"\n[bold]Finished processing:[/bold] [green]{success_count} succeeded[/green], [red]{failure_count} failed[/red]. Total PII findings redacted: [bold magenta]{total_findings}[/bold magenta]")


@cli.command("entities")
def entities_cmd():
    """List all supported default PII entity types."""
    table = Table(title="[bold magenta]Supported PII Entities[/bold magenta]", show_header=True)
    table.add_column("Entity Type", style="bold cyan")
    table.add_column("Description", style="dim")

    entity_descriptions = {
        "PERSON": "Person names (e.g. John Doe, Erin Davis)",
        "EMAIL_ADDRESS": "Email addresses (e.g. john@example.com)",
        "PHONE_NUMBER": "Phone and telephone numbers",
        "LOCATION": "Geographic locations, cities, countries",
        "STREET_ADDRESS": "Street addresses (e.g. 123 Main St)",
        "US_SSN": "US Social Security Numbers",
        "CREDIT_CARD": "Credit card and debit card numbers",
        "IP_ADDRESS": "IPv4 and IPv6 network addresses",
        "IBAN_CODE": "International Bank Account Numbers",
        "US_BANK_NUMBER": "US Bank account numbers",
        "US_DRIVER_LICENSE": "US Driver's license numbers",
        "US_PASSPORT": "US Passport numbers",
    }

    for entity in DEFAULT_ENTITIES:
        desc = entity_descriptions.get(entity, "Standard Presidio entity recognizer")
        table.add_row(entity, desc)

    console.print(table)
