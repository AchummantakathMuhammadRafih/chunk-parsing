"""Data models and schemas for Markdown Redactor."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import time


@dataclass
class RedactionFinding:
    """Represents a single detected PII finding."""

    entity_type: str
    start: int
    end: int
    score: float
    original_text: Optional[str] = None


@dataclass
class RedactionResult:
    """Represents the outcome of a markdown file redaction."""

    input_path: Path
    output_path: Path
    findings_count: int
    entity_counts: Dict[str, int] = field(default_factory=dict)
    execution_time: float = 0.0
    original_size_bytes: int = 0
    redacted_size_bytes: int = 0
    success: bool = True
    error_message: Optional[str] = None
