"""Configuration settings for Markdown PII Redactor."""

from typing import List, Optional
from pydantic import BaseModel, Field

from markdown_redactor.config.constants import (
    DEFAULT_ENTITIES,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_MASK_CHAR,
    DEFAULT_CHARS_TO_MASK,
)


class RedactionConfig(BaseModel):
    """Configuration options for PII identification and anonymization."""

    entities: List[str] = Field(
        default_factory=lambda: list(DEFAULT_ENTITIES),
        description="List of PII entity types to detect and redact.",
    )
    score_threshold: float = Field(
        default=DEFAULT_SCORE_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Confidence score threshold for Presidio Analyzer.",
    )
    language: str = Field(
        default="en",
        description="Language code for analyzer models.",
    )
    mask_char: str = Field(
        default=DEFAULT_MASK_CHAR,
        description="Masking character to replace sensitive characters with.",
    )
    chars_to_mask: int = Field(
        default=DEFAULT_CHARS_TO_MASK,
        description="Number of characters to mask (use large int for full replacement).",
    )
    custom_recognizers: bool = Field(
        default=True,
        description="Whether to register custom recognizers (e.g. STREET_ADDRESS).",
    )
    ignore_code_blocks: bool = Field(
        default=True,
        description="Whether to preserve code blocks and inline code untouched.",
    )
    ignore_image_urls: bool = Field(
        default=True,
        description="Whether to preserve image markdown urls and link targets.",
    )
