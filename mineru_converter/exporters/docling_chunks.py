"""Docling hybrid chunking of MinerU Markdown with base64 images from the MinerU content list."""

import base64
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mineru_converter.config.constants import IMAGE_PLACEHOLDER_PATTERN, SUFFIX_DOCLING_CHUNKS
from mineru_converter.config.settings import ConversionConfig
from mineru_converter.core.docling_client import DoclingClient
from mineru_converter.models.schemas import OutputFileManifest
from mineru_converter.utils.logging_utils import get_logger

logger = get_logger()

_PLACEHOLDER_RE = re.compile(IMAGE_PLACEHOLDER_PATTERN, re.IGNORECASE)
_PICTURE_REF_RE = re.compile(r"^#/pictures/(\d+)$")


def load_content_list_images(content_list_path: Path) -> List[Dict[str, Any]]:
    """Return image entries from a MinerU V1 content list in document order."""
    with open(content_list_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    return [item for item in items if isinstance(item, dict) and item.get("type") == "image"]


def _clean_label_part(value: Any) -> str:
    text = " ".join(str(value).split())
    return text.replace("[", "(").replace("]", ")")


def build_image_label(captions: List[Any], footnotes: List[Any]) -> str:
    """Build `captions, ... . footnotes, ...` text for the image placeholder."""
    caption_text = ", ".join(p for p in (_clean_label_part(c) for c in captions or []) if p)
    footnote_text = ", ".join(p for p in (_clean_label_part(f) for f in footnotes or []) if p)
    return ". ".join(p for p in (caption_text, footnote_text) if p)


def _encode_image(base_dir: Path, img_path: Optional[str]) -> Optional[str]:
    if not img_path:
        return None
    root = base_dir.resolve()
    target = (root / img_path).resolve()
    # img_path comes from a JSON file; keep reads inside the output directory
    if root not in target.parents or not target.is_file():
        return None
    return base64.b64encode(target.read_bytes()).decode("ascii")


def attach_images_to_chunks(
    chunks: List[Dict[str, Any]],
    content_images: List[Dict[str, Any]],
    base_dir: Path,
) -> int:
    """
    Rewrite image placeholders in each chunk's text and fill `images` with base64 strings.

    The Nth placeholder across all chunks maps to the Nth content-list image.
    `images` stays 1:1 with placeholders; unresolvable images are "".
    Returns the number of non-empty images attached.
    """
    counter = 0
    attached = 0

    for chunk in sorted(chunks, key=lambda c: c.get("chunk_index", 0)):
        images: List[str] = []
        assigned: List[int] = []

        def _replace(match: re.Match) -> str:
            nonlocal counter
            idx = counter
            counter += 1
            assigned.append(idx)
            if idx >= len(content_images):
                images.append("")
                return match.group(0)

            entry = content_images[idx]
            encoded = _encode_image(base_dir, entry.get("img_path"))
            if encoded is None:
                logger.warning(f"Image file not found for placeholder #{idx}: {entry.get('img_path')}")
            images.append(encoded or "")

            label = build_image_label(entry.get("image_caption"), entry.get("image_footnote"))
            return f"![{label}]" if label else match.group(0)

        text = chunk.get("text") or ""
        chunk["text"] = _PLACEHOLDER_RE.sub(_replace, text).strip()
        chunk["images"] = images
        attached += sum(1 for img in images if img)

        picture_refs = [
            int(m.group(1))
            for ref in chunk.get("doc_items") or []
            if isinstance(ref, str) and (m := _PICTURE_REF_RE.match(ref))
        ]
        if picture_refs and picture_refs != assigned:
            logger.warning(
                f"Chunk {chunk.get('chunk_index')}: placeholder order {assigned} "
                f"differs from doc_items pictures {picture_refs}"
            )

    if counter != len(content_images):
        logger.warning(
            f"Docling produced {counter} image placeholders but the content list has "
            f"{len(content_images)} images; mapping may be misaligned"
        )
    return attached


def run_docling_chunking(
    manifest: OutputFileManifest,
    config: ConversionConfig,
) -> Tuple[Path, int, int]:
    """Chunk the MinerU Markdown via docling-serve and write `<stem>_docling_chunks.json`."""
    if not manifest.markdown_path or not manifest.markdown_path.exists():
        raise FileNotFoundError("Markdown output not found; cannot run Docling chunking")
    if not manifest.content_list_v1_path or not manifest.content_list_v1_path.exists():
        raise FileNotFoundError("Content list (_content_list.json) not found; cannot attach images")

    start = time.time()
    client = DoclingClient(
        server_url=config.docling_url,
        timeout=config.docling_timeout,
        max_tokens=config.docling_max_tokens,
        tokenizer=config.docling_tokenizer,
    )
    markdown_text = manifest.markdown_path.read_text(encoding="utf-8")
    chunks = client.chunk_markdown(markdown_text, filename=manifest.markdown_path.name)

    content_images = load_content_list_images(manifest.content_list_v1_path)
    attached = attach_images_to_chunks(chunks, content_images, manifest.output_directory)

    output_path = manifest.output_directory / f"{manifest.document_name}{SUFFIX_DOCLING_CHUNKS}"
    payload = {
        "document_name": manifest.document_name,
        "total_chunks": len(chunks),
        "total_images_attached": attached,
        "processing_time_seconds": round(time.time() - start, 3),
        "chunks": chunks,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Docling chunking: {len(chunks)} chunks, {attached} images attached -> {output_path.name}")
    return output_path, len(chunks), attached
