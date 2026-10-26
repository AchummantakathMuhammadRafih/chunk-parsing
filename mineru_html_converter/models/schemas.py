"""Data schemas for HTML conversion results."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class HTMLConversionResult(BaseModel):
    """Result of converting a PDF document to HTML."""

    success: bool = Field(description="Whether the conversion succeeded.")
    input_file: Path = Field(description="Original input PDF file path.")
    output_html_file: Path = Field(description="Generated HTML file path.")
    document_name: str = Field(description="Sanitized document title/stem.")
    asset_paths: List[Path] = Field(default_factory=list, description="Extracted external asset paths (images, etc).")
    embedded_images_count: int = Field(default=0, description="Number of images converted to embedded base64 data URIs.")
    file_size_bytes: int = Field(default=0, description="Size of generated HTML file in bytes.")
    page_count: Optional[int] = Field(default=None, description="Number of pages converted if determinable.")
    duration_seconds: float = Field(default=0.0, description="Total execution time in seconds.")
    error_message: Optional[str] = Field(default=None, description="Error message if conversion failed.")
    converted_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of conversion.")
