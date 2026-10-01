"""Postprocessing utilities for extracted Markdown and MinerU artifacts."""

from pathlib import Path
from typing import Optional
import shutil

from mineru_converter.models.schemas import OutputFileManifest
from mineru_converter.utils.logging_utils import get_logger

logger = get_logger()


def create_standard_aliases(
    manifest: OutputFileManifest,
    create_v_aliases: bool = True
) -> None:
    """
    Create convenient file aliases for content lists if desired (e.g., _v1list.json, _v2list.json).
    
    Args:
        manifest: Output manifest containing resolved file paths.
        create_v_aliases: If True, creates copy/symlink aliases for easier access.
    """
    if not create_v_aliases or not manifest.output_directory:
        return

    doc_dir = manifest.output_directory
    stem = manifest.document_name

    # Create v1 alias if needed
    if manifest.content_list_v1_path and manifest.content_list_v1_path.exists():
        v1_alias = doc_dir / f"{stem}_v1list.json"
        if not v1_alias.exists():
            try:
                shutil.copy2(manifest.content_list_v1_path, v1_alias)
            except Exception as exc:
                logger.debug(f"Could not create v1 alias: {exc}")

    # Create v2 alias if needed
    if manifest.content_list_v2_path and manifest.content_list_v2_path.exists():
        v2_alias = doc_dir / f"{stem}_v2list.json"
        if not v2_alias.exists():
            try:
                shutil.copy2(manifest.content_list_v2_path, v2_alias)
            except Exception as exc:
                logger.debug(f"Could not create v2 alias: {exc}")
