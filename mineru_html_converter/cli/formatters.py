"""Rich terminal presentation formatters."""

from rich.panel import Panel
from rich.table import Table

from mineru_html_converter.models.schemas import HTMLConversionResult
from mineru_html_converter.utils.file_utils import format_file_size
from mineru_html_converter.utils.logging_utils import console


def print_banner():
    """Print the CLI application header."""
    banner_text = (
        "[bold cyan]MinerU Document to HTML Converter[/bold cyan]\n"
        "[dim]High-fidelity document layout engine rendering semantic, responsive HTML (PDF, DOCX, PPTX, XLSX)[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def print_conversion_result(result: HTMLConversionResult):
    """Print a styled summary table for a conversion result."""
    table = Table(title="Conversion Summary", border_style="blue", show_header=True)
    table.add_column("Property", style="bold white", width=22)
    table.add_column("Value", style="cyan")

    table.add_row("Status", "[bold green]Success[/bold green]" if result.success else "[bold red]Failed[/bold red]")
    table.add_row("Input File", str(result.input_file))
    table.add_row("Output HTML", str(result.output_html_file))
    table.add_row("File Size", format_file_size(result.file_size_bytes))
    table.add_row("Embedded Images", str(result.embedded_images_count))
    table.add_row("Duration", f"{result.duration_seconds:.2f}s")

    if result.error_message:
        table.add_row("Error", f"[red]{result.error_message}[/red]")

    console.print(table)
