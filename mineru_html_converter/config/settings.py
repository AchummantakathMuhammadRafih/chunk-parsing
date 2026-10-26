"""Configuration models and dataclasses for MinerU HTML converter."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from mineru_html_converter.config.constants import DEFAULT_OUTPUT_DIR, RenderModeEnum, ThemeEnum


class HTMLConversionConfig(BaseModel):
    """Configuration options for converting PDF to HTML via MinerU."""
    
    output_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
        description="Directory where generated HTML files and assets are saved."
    )
    pages: Optional[str] = Field(
        default=None,
        description="Page range specification (e.g., '1-5,8', '1-10', 'all'). If None, processes all pages."
    )
    mode: RenderModeEnum = Field(
        default=RenderModeEnum.DEFAULT,
        description="Render mode: 'default' (responsive article layout) or 'full' (page-based container layout)."
    )
    embed_images: bool = Field(
        default=True,
        description="Embed extracted images directly into HTML as base64 data URIs for 100% self-contained output."
    )
    standalone: bool = Field(
        default=True,
        description="Generate complete standalone HTML documents with doctype, head, and styling."
    )
    document_title: Optional[str] = Field(
        default=None,
        description="Custom document title for the HTML head. Defaults to document filename stem."
    )
    theme: ThemeEnum = Field(
        default=ThemeEnum.MODERN,
        description="Visual presentation styling theme applied to the rendered HTML document."
    )
    add_toc: bool = Field(
        default=True,
        description="Generate an interactive floating Table of Contents from headings."
    )
    overwrite: bool = Field(
        default=True,
        description="Overwrite existing output files."
    )
