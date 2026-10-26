"""File and path helper utilities."""

import re
from pathlib import Path
from typing import List

from mineru_html_converter.config.constants import SUPPORTED_EXTENSIONS


def sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent invalid characters across operating systems."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
    return cleaned.strip(" ._") or "document"


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, creating parent folders if needed."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_supported_documents(target: Path, recursive: bool = True) -> List[Path]:
    """Find all supported documents (PDF, DOCX, PPTX, XLSX, etc.) in a file or directory path."""
    target_path = Path(target).resolve()
    if target_path.is_file():
        if target_path.suffix.lower() in {ext.lower() for ext in SUPPORTED_EXTENSIONS}:
            return [target_path]
        return []
        
    pattern = "**/*" if recursive else "*"
    found = []
    for p in target_path.glob(pattern):
        if p.is_file() and p.suffix.lower() in {ext.lower() for ext in SUPPORTED_EXTENSIONS}:
            found.append(p)
    return sorted(found)


def find_pdf_files(target: Path, recursive: bool = True) -> List[Path]:
    """Backward compatibility alias for find_supported_documents."""
    return find_supported_documents(target, recursive)


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable string (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
