"""Click CLI commands for media transcription."""

import os
import sys
from pathlib import Path
from typing import Optional, List
import click

from media_transcriber.config.settings import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_MODEL_SIZE,
    DEFAULT_DEVICE,
    WhisperModelSize,
    OutputFormat,
)
from media_transcriber.core.transcriber import MediaTranscriber
from media_transcriber.exporters.writers import TranscriptionWriter
from media_transcriber.cli.formatters import (
    print_banner,
    print_transcription_preview,
    print_result_summary,
    print_batch_summary,
)
from media_transcriber.utils.audio_utils import scan_media_files, is_supported_media
from media_transcriber.utils.logging_utils import console, setup_logger


@click.group(invoke_without_command=False)
@click.version_option(version="1.0.0", prog_name="media-transcriber")
def cli():
    """Media Transcriber - Extract speech to timestamped text from MP3, MP4, and other audio/video formats."""
    pass


@cli.command("transcribe")
@click.argument("media_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o", "--output", "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Target directory for output files."
)
@click.option(
    "-m", "--model", "model_size",
    type=click.Choice([m.value for m in WhisperModelSize], case_sensitive=False),
    default=DEFAULT_MODEL_SIZE.value,
    show_default=True,
    help="Whisper model size to use."
)
@click.option(
    "-f", "--format", "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.ALL.value,
    show_default=True,
    help="Output format: txt (timestamped), raw_txt (plain text without timestamps), srt, vtt, json, tsv, or all."
)
@click.option(
    "-l", "--language",
    type=str,
    default=None,
    help="Media language code (e.g. 'en', 'es', 'fr', 'de'). Defaults to auto-detect."
)
@click.option(
    "-d", "--device",
    type=click.Choice(["auto", "cpu", "cuda"], case_sensitive=False),
    default=DEFAULT_DEVICE,
    show_default=True,
    help="Compute device for transcription."
)
@click.option(
    "--word-timestamps",
    is_flag=True,
    default=False,
    help="Extract detailed word-level timestamps in addition to segment timestamps."
)
@click.option(
    "--translate",
    is_flag=True,
    default=False,
    help="Translate the spoken audio to English instead of just transcribing."
)
@click.option(
    "--preview/--no-preview",
    default=True,
    show_default=True,
    help="Display transcription segment preview in console."
)
def transcribe_cmd(
    media_file: Path,
    output_dir: Path,
    model_size: str,
    output_format: str,
    language: Optional[str],
    device: str,
    word_timestamps: bool,
    translate: bool,
    preview: bool,
):
    """Transcribe a single audio or video file (MP3, MP4, WAV, M4A, etc.) with timestamps."""
    print_banner()

    if not is_supported_media(media_file):
        console.print(f"[bold red]Error:[/bold red] Unsupported file format '{media_file.suffix}'. Supported: MP3, MP4, WAV, M4A, MKV, MOV, etc.")
        sys.exit(1)

    task = "translate" if translate else "transcribe"
    console.print(f"[bold cyan]File:[/bold cyan] {media_file.name}")
    console.print(f"[bold cyan]Model:[/bold cyan] {model_size} | [bold cyan]Task:[/bold cyan] {task} | [bold cyan]Device:[/bold cyan] {device}")

    with console.status("[bold green]Transcribing media with timestamps... (this may take a moment)"):
        transcriber = MediaTranscriber(model_name=model_size, device=device)
        result = transcriber.transcribe(
            file_path=media_file,
            language=language,
            task=task,
            word_timestamps=word_timestamps,
        )

    base_name = media_file.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    if output_format == OutputFormat.ALL.value:
        saved_files = TranscriptionWriter.export_all(result, output_dir, base_name)
    elif output_format == OutputFormat.TXT.value:
        saved_files["txt"] = TranscriptionWriter.write_txt_with_timestamps(result, output_dir / f"{base_name}.txt")
    elif output_format == OutputFormat.RAW_TXT.value:
        saved_files["raw_txt"] = TranscriptionWriter.write_plain_text(result, output_dir / f"{base_name}.raw.txt")
    elif output_format == OutputFormat.SRT.value:
        saved_files["srt"] = TranscriptionWriter.write_srt(result, output_dir / f"{base_name}.srt")
    elif output_format == OutputFormat.VTT.value:
        saved_files["vtt"] = TranscriptionWriter.write_vtt(result, output_dir / f"{base_name}.vtt")
    elif output_format == OutputFormat.JSON.value:
        saved_files["json"] = TranscriptionWriter.write_json(result, output_dir / f"{base_name}.json")
    elif output_format == OutputFormat.TSV.value:
        saved_files["tsv"] = TranscriptionWriter.write_tsv(result, output_dir / f"{base_name}.tsv")

    if preview and result.segments:
        print_transcription_preview(result)

    print_result_summary(result, saved_files)


@cli.command("batch")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o", "--output", "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Target directory for output files."
)
@click.option(
    "-m", "--model", "model_size",
    type=click.Choice([m.value for m in WhisperModelSize], case_sensitive=False),
    default=DEFAULT_MODEL_SIZE.value,
    show_default=True,
    help="Whisper model size to use."
)
@click.option(
    "-f", "--format", "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.ALL.value,
    show_default=True,
    help="Output format: txt (timestamped), raw_txt (plain text), srt, vtt, json, tsv, or all."
)
@click.option(
    "-l", "--language",
    type=str,
    default=None,
    help="Media language code. Defaults to auto-detect."
)
@click.option(
    "-d", "--device",
    type=click.Choice(["auto", "cpu", "cuda"], case_sensitive=False),
    default=DEFAULT_DEVICE,
    show_default=True,
    help="Compute device for transcription."
)
@click.option(
    "-r", "--recursive",
    is_flag=True,
    default=False,
    help="Recursively scan input directory for media files."
)
def batch_cmd(
    input_dir: Path,
    output_dir: Path,
    model_size: str,
    output_format: str,
    language: Optional[str],
    device: str,
    recursive: bool,
):
    """Batch transcribe all MP3, MP4, and media files in a directory."""
    print_banner()

    files = scan_media_files(input_dir, recursive=recursive)
    if not files:
        console.print(f"[bold yellow]No supported media files found in:[/bold yellow] {input_dir}")
        return

    console.print(f"[bold cyan]Found {len(files)} media file(s) to transcribe.[/bold cyan]")

    with console.status(f"[bold green]Loading Whisper model '{model_size}'..."):
        transcriber = MediaTranscriber(model_name=model_size, device=device)

    results: List[TranscriptionResult] = []
    failed: List[str] = []

    for idx, f in enumerate(files, 1):
        console.print(f"\n[bold][{idx}/{len(files)}] Processing {f.name}...[/bold]")
        try:
            res = transcriber.transcribe(f, language=language)
            base_name = f.stem
            
            if output_format == OutputFormat.ALL.value:
                TranscriptionWriter.export_all(res, output_dir, base_name)
            elif output_format == OutputFormat.TXT.value:
                TranscriptionWriter.write_txt_with_timestamps(res, output_dir / f"{base_name}.txt")
            elif output_format == OutputFormat.RAW_TXT.value:
                TranscriptionWriter.write_plain_text(res, output_dir / f"{base_name}.raw.txt")
            elif output_format == OutputFormat.SRT.value:
                TranscriptionWriter.write_srt(res, output_dir / f"{base_name}.srt")
            elif output_format == OutputFormat.VTT.value:
                TranscriptionWriter.write_vtt(res, output_dir / f"{base_name}.vtt")
            elif output_format == OutputFormat.JSON.value:
                TranscriptionWriter.write_json(res, output_dir / f"{base_name}.json")
            elif output_format == OutputFormat.TSV.value:
                TranscriptionWriter.write_tsv(res, output_dir / f"{base_name}.tsv")

            results.append(res)
            console.print(f"[green][OK] Completed {f.name} ({len(res.segments)} segments)[/green]")
        except Exception as e:
            console.print(f"[bold red][ERROR] Failed {f.name}: {e}[/bold red]")
            failed.append(f.name)

    print_batch_summary(results, failed)
