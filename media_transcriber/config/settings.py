"""Configuration constants and settings for media_transcriber."""

from enum import Enum
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field


class WhisperModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V3 = "large-v3"


class OutputFormat(str, Enum):
    ALL = "all"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"
    TSV = "tsv"


DEFAULT_OUTPUT_DIR = Path("output/transcriptions")
DEFAULT_MODEL_SIZE = WhisperModelSize.BASE
DEFAULT_DEVICE = "auto"
