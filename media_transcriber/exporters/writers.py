"""Writers for exporting timestamped transcriptions to various formats (TXT, SRT, VTT, JSON, TSV)."""

import json
from pathlib import Path
from typing import Dict, Any

from media_transcriber.models.schemas import TranscriptionResult
from media_transcriber.utils.audio_utils import format_timestamp, format_timestamp_short


class TranscriptionWriter:
    """Handles writing transcription results to different file formats."""

    @staticmethod
    def write_txt_with_timestamps(result: TranscriptionResult, out_path: Path) -> Path:
        """Write human-readable text with timestamp brackets like [00:01 - 00:05] Text."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        lines.append(f"# Transcription: {Path(result.source_file).name}")
        lines.append(f"# Media Type: {result.media_type.upper()} | Language: {result.language}")
        if result.duration_seconds:
            lines.append(f"# Duration: {format_timestamp_short(result.duration_seconds)}")
        lines.append("")

        for seg in result.segments:
            start_str = format_timestamp_short(seg.start)
            end_str = format_timestamp_short(seg.end)
            text_clean = seg.text.strip()
            lines.append(f"[{start_str} -> {end_str}] {text_clean}")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    @staticmethod
    def write_srt(result: TranscriptionResult, out_path: Path) -> Path:
        """Write SubRip Subtitle (.srt) format."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blocks = []
        for i, seg in enumerate(result.segments, 1):
            start_str = format_timestamp(seg.start, srt=True)
            end_str = format_timestamp(seg.end, srt=True)
            text_clean = seg.text.strip()
            blocks.append(f"{i}\n{start_str} --> {end_str}\n{text_clean}\n")

        out_path.write_text("\n".join(blocks), encoding="utf-8")
        return out_path

    @staticmethod
    def write_vtt(result: TranscriptionResult, out_path: Path) -> Path:
        """Write WebVTT (.vtt) format."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blocks = ["WEBVTT\n"]
        for seg in result.segments:
            start_str = format_timestamp(seg.start, srt=False)
            end_str = format_timestamp(seg.end, srt=False)
            text_clean = seg.text.strip()
            blocks.append(f"{start_str} --> {end_str}\n{text_clean}\n")

        out_path.write_text("\n".join(blocks), encoding="utf-8")
        return out_path

    @staticmethod
    def write_tsv(result: TranscriptionResult, out_path: Path) -> Path:
        """Write Tab-Separated Values (.tsv) format."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["start\tend\ttext"]
        for seg in result.segments:
            start_ms = int(round(seg.start * 1000))
            end_ms = int(round(seg.end * 1000))
            text_clean = seg.text.strip().replace("\t", " ")
            lines.append(f"{start_ms}\t{end_ms}\t{text_clean}")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    @staticmethod
    def write_json(result: TranscriptionResult, out_path: Path) -> Path:
        """Write detailed JSON format."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data = result.model_dump()
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    @classmethod
    def export_all(cls, result: TranscriptionResult, output_dir: Path, base_name: str) -> Dict[str, Path]:
        """Export transcription to all supported formats."""
        output_dir.mkdir(parents=True, exist_ok=True)
        generated = {}
        generated["txt"] = cls.write_txt_with_timestamps(result, output_dir / f"{base_name}.txt")
        generated["srt"] = cls.write_srt(result, output_dir / f"{base_name}.srt")
        generated["vtt"] = cls.write_vtt(result, output_dir / f"{base_name}.vtt")
        generated["tsv"] = cls.write_tsv(result, output_dir / f"{base_name}.tsv")
        generated["json"] = cls.write_json(result, output_dir / f"{base_name}.json")
        return generated
