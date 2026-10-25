"""Docling hybrid chunking of MinerU Markdown with base64 images from the MinerU content list."""

import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mineru_converter.config.constants import DOCLING_CHUNKS_FILE_NAME, IMAGE_PLACEHOLDER_PATTERN
from mineru_converter.config.settings import ConversionConfig
from mineru_converter.core.docling_client import DoclingClient
from mineru_converter.models.schemas import OutputFileManifest
from mineru_converter.utils.logging_utils import get_logger
from mineru_converter.utils.redaction import mask_personal_info

logger = get_logger()

_PLACEHOLDER_RE = re.compile(IMAGE_PLACEHOLDER_PATTERN, re.IGNORECASE)
_PICTURE_REF_RE = re.compile(r"^#/pictures/(\d+)$")


META_IMAGE_PATTERN = r"META\^IMG_\d+\^END"
_META_IMAGE_RE = re.compile(META_IMAGE_PATTERN)
_MARKDOWN_IMAGE_RE = re.compile(
    r"!\[(.*?)\]\((images/[^)]+)\)|<img[^>]+src=[\x22\x27](images/[^\x22\x27]+)[\x22\x27][^>]*>"
)


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
    mime_type = mimetypes.guess_type(target.name)[0] or "image/jpeg"
    encoded = base64.b64encode(target.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def preprocess_markdown_images(
    markdown_text: str,
    content_images: List[Dict[str, Any]],
    base_dir: Path,
) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """
    Capture all Markdown/HTML images into a map with unique keys (META^IMG_1^END, META^IMG_2^END, ...).
    Replaces each image reference in the text with its unique placeholder so docling-serve preserves it.
    """
    cl_by_path = {
        item.get("img_path"): item
        for item in content_images
        if isinstance(item, dict) and item.get("img_path")
    }

    image_map: Dict[str, Dict[str, Any]] = {}
    counter = 0

    def _replace(match: re.Match) -> str:
        nonlocal counter
        counter += 1
        key = f"META^IMG_{counter}^END"

        # match.group(2) is markdown path, match.group(3) is html path
        if match.group(2):
            alt = match.group(1) or ""
            img_path = match.group(2)
        else:
            alt = ""
            img_path = match.group(3)

        cl_entry = cl_by_path.get(img_path)
        label = ""
        if cl_entry:
            label = build_image_label(cl_entry.get("image_caption"), cl_entry.get("image_footnote"))
        if not label and alt.strip():
            label = _clean_label_part(alt.strip())

        image_map[key] = {
            "img_path": img_path,
            "label": label,
            "data_url": _encode_image(base_dir, img_path) or "",
        }
        return f"\n\n{key}\n\n"

    preprocessed_text = _MARKDOWN_IMAGE_RE.sub(_replace, markdown_text)
    return preprocessed_text, image_map


def link_images_from_map(
    chunks: List[Dict[str, Any]],
    image_map: Dict[str, Dict[str, Any]],
) -> int:
    """
    Link images from the captured image_map back into the chunks returned by docling-serve.
    Populates `images` list with base64 data URLs and rewrites the unique tokens to `![label]` or `![IMAGE]`.
    """
    attached = 0

    def _make_repl():
        def _sub(m: re.Match) -> str:
            k = m.group(0)
            item = image_map.get(k)
            if not item:
                return "![IMAGE]"
            lbl = item["label"]
            return f"![{lbl}]" if lbl else "![IMAGE]"
        return _sub

    for chunk in chunks:
        chunk_images: List[str] = []
        text = chunk.get("text") or ""

        for m in _META_IMAGE_RE.finditer(text):
            item = image_map.get(m.group(0))
            chunk_images.append(item["data_url"] if item else "")

        chunk["text"] = _META_IMAGE_RE.sub(_make_repl(), text).strip()
        chunk["images"] = chunk_images
        attached += sum(1 for img in chunk_images if img)

        if "raw_text" in chunk and isinstance(chunk["raw_text"], str):
            chunk["raw_text"] = _META_IMAGE_RE.sub(_make_repl(), chunk["raw_text"]).strip()

    return attached


def attach_images_to_chunks(
    chunks: List[Dict[str, Any]],
    content_images: List[Dict[str, Any]],
    base_dir: Path,
) -> int:
    """
    Rewrite image placeholders in each chunk's text and fill `images` with data URLs.

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
    """Chunk MinerU Markdown, sanitize it, and write `docling_chunks.json`."""
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
    content_images = load_content_list_images(manifest.content_list_v1_path) if config.dump_images else []

    # 1. Preprocess images into unique META^IMG markers before sending to docling-serve (if enabled)
    if config.dump_images and content_images:
        preprocessed_md, image_map = preprocess_markdown_images(
            markdown_text=markdown_text,
            content_images=content_images,
            base_dir=manifest.output_directory,
        )
    else:
        preprocessed_md = markdown_text
        image_map = {}

    # 2. Chunk with docling-serve
    chunks = client.chunk_markdown(preprocessed_md, filename=manifest.markdown_path.name)

    # 3. Link images from the map back into chunks (if enabled)
    if config.dump_images:
        if image_map:
            attached = link_images_from_map(chunks, image_map)
        else:
            # Fallback to standard attachment if no markdown/html images were preprocessed
            attached = attach_images_to_chunks(chunks, content_images, manifest.output_directory)
    else:
        attached = 0
        for chunk in chunks:
            chunk["images"] = []

    for chunk in chunks:
        for key in ("text", "raw_text"):
            value = chunk.get(key)
            if isinstance(value, str):
                chunk[key] = mask_personal_info(value)
        chunk.pop("doc_items", None)
        chunk.pop("metadata", None)

    output_path = manifest.output_directory / DOCLING_CHUNKS_FILE_NAME
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
