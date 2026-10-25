"""Audio and media helper utilities."""

import os
from pathlib import Path
from typing import List, Tuple

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv"}
SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS


def is_supported_media(file_path: Path) -> bool:
    """Check if the given file has a supported media extension."""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_media_type(file_path: Path) -> str:
    """Return whether the file is audio or video."""
    ext = file_path.suffix.lower()
    if ext in SUPPORTED_AUDIO_EXTENSIONS:
        return "audio"
    if ext in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def format_timestamp(seconds: float, srt: bool = False) -> str:
    """Format seconds into HH:MM:SS.mmm or HH:MM:SS,mmm for SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999

    delimiter = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{delimiter}{millis:03d}"


def format_timestamp_short(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS without milliseconds."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def scan_media_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Scan directory for supported audio and video files."""
    if not directory.exists() or not directory.is_dir():
        return []

    pattern = "**/*" if recursive else "*"
    files = [p for p in directory.glob(pattern) if p.is_file() and is_supported_media(p)]
    return sorted(files)
