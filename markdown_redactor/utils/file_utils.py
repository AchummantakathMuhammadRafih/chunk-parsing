"""File and path utilities for markdown_redactor."""

from pathlib import Path
from typing import List


def find_markdown_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Find all markdown files (*.md, *.markdown) in directory."""
    patterns = ["*.md", "*.markdown"]
    files: List[Path] = []
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return files

    for pattern in patterns:
        if recursive:
            files.extend(dir_path.rglob(pattern))
        else:
            files.extend(dir_path.glob(pattern))

    return sorted(list(set(files)))
