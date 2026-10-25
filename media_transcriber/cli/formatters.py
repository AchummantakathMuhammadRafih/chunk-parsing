"""Terminal UI formatters using Rich."""

from pathlib import Path
from typing import Dict, List
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from media_transcriber.models.schemas import TranscriptionResult
from media_transcriber.utils.audio_utils import format_timestamp_short
from media_transcriber.utils.logging_utils import console


def print_banner():
    """Print welcoming CLI banner."""
    title = Text("Media Transcriber CLI", style="bold cyan")
    subtitle = Text("Speech-to-Text with Timestamps for MP3, MP4 & Audio/Video", style="dim italic")
    console.print(Panel(Text.assemble(title, "\n", subtitle), border_style="cyan"))


def print_transcription_preview(result: TranscriptionResult, max_segments: int = 8):
    """Print formatted segment preview table to terminal."""
    table = Table(title=f"Transcription Segments Preview ({Path(result.source_file).name})", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Start", style="green", width=10)
    table.add_column("End", style="green", width=10)
    table.add_column("Transcribed Text", style="bright_white")

    num_display = min(len(result.segments), max_segments)
    for i in range(num_display):
        seg = result.segments[i]
        start_fmt = format_timestamp_short(seg.start)
        end_fmt = format_timestamp_short(seg.end)
        table.add_row(str(i + 1), start_fmt, end_fmt, seg.text.strip())

    console.print(table)
    if len(result.segments) > max_segments:
        console.print(f"[dim]... and {len(result.segments) - max_segments} more segments.[/dim]")


def print_result_summary(result: TranscriptionResult, saved_files: Dict[str, Path]):
    """Print summary details and output file locations."""
    summary_text = (
        f"[bold green][OK] Transcription Complete![/bold green]\n"
        f"[bold]Media File:[/bold] {result.source_file}\n"
        f"[bold]Type:[/bold] {result.media_type.upper()} | [bold]Detected Language:[/bold] {result.language}\n"
        f"[bold]Total Segments:[/bold] {len(result.segments)} | [bold]Duration:[/bold] {format_timestamp_short(result.duration_seconds or 0)}\n\n"
        f"[bold cyan]Generated Files:[/bold cyan]\n"
    )
    for fmt, path in saved_files.items():
        summary_text += f" * [{fmt.upper()}] {path.resolve()}\n"

    console.print(Panel(summary_text.strip(), title="Result Summary", border_style="green"))


def print_batch_summary(results: List[TranscriptionResult], failed: List[str]):
    """Print overall batch summary table."""
    table = Table(title="Batch Transcription Summary", show_header=True, header_style="bold blue")
    table.add_column("File", style="bold")
    table.add_column("Type", width=8)
    table.add_column("Language", width=10)
    table.add_column("Duration", width=10)
    table.add_column("Segments", justify="right", width=10)

    for r in results:
        table.add_row(
            Path(r.source_file).name,
            r.media_type.upper(),
            r.language,
            format_timestamp_short(r.duration_seconds or 0),
            str(len(r.segments)),
        )

    console.print(table)
    if failed:
        console.print(f"[bold red]Failed files ({len(failed)}):[/bold red] {', '.join(failed)}")
