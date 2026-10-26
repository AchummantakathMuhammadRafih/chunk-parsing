"""Formatters and rich tables for markdown_redactor CLI."""

from rich.panel import Panel
from rich.table import Table

from markdown_redactor.models.schemas import RedactionResult
from markdown_redactor.utils.logging_utils import console


def print_banner() -> None:
    """Print the CLI banner."""
    title = "[bold magenta]Markdown PII Redactor[/bold magenta] [cyan]v1.0.0[/cyan]"
    subtitle = "[dim]Microsoft Presidio Privacy Anonymizer & Star-Masking CLI[/dim]"
    panel = Panel(
        f"{title}\n{subtitle}",
        border_style="magenta",
        expand=False,
    )
    console.print(panel)


def print_redaction_result(result: RedactionResult) -> None:
    """Print the result of a single file redaction."""
    if not result.success:
        console.print(f"[bold red]✗ Redaction failed:[/bold red] {result.error_message}")
        return

    table = Table(title="[bold green]Redaction Summary[/bold green]", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("Input File", str(result.input_path))
    table.add_row("Output File", str(result.output_path))
    table.add_row("Total Redacted Findings", str(result.findings_count))
    table.add_row("Execution Time", f"{result.execution_time:.2f}s")
    table.add_row("Original Size", f"{result.original_size_bytes:,} bytes")
    table.add_row("Redacted Size", f"{result.redacted_size_bytes:,} bytes")

    console.print(table)

    if result.entity_counts:
        entity_table = Table(title="[bold yellow]Entities Redacted[/bold yellow]", show_header=True, header_style="bold yellow")
        entity_table.add_column("Entity Type", style="bold")
        entity_table.add_column("Count", justify="right")

        for entity, count in sorted(result.entity_counts.items(), key=lambda x: x[1], reverse=True):
            entity_table.add_row(entity, str(count))

        console.print(entity_table)
    else:
        console.print("[dim green]No sensitive PII entities detected in this file.[/dim green]")
