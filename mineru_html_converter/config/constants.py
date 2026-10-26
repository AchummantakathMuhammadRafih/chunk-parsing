"""Constants and default parameters for MinerU HTML converter."""

from enum import Enum
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("output/html")

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".doc",
    ".ppt",
    ".xls",
    ".csv",
    ".tsv",
    ".epub",
}

class RenderModeEnum(str, Enum):
    """HTML rendering mode."""
    DEFAULT = "default"  # Clean responsive article layout
    FULL = "full"        # Full structured layout with page containers & explicit page breaks

class ThemeEnum(str, Enum):
    """Visual theme for the HTML viewer."""
    MODERN = "modern"
    DARK = "dark"
    MINIMAL = "minimal"
    READABLE = "readable"
