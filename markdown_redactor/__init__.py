"""Markdown PII Redaction package using Microsoft Presidio."""

from markdown_redactor.core.redactor import MarkdownRedactor
from markdown_redactor.config.settings import RedactionConfig

__version__ = "1.0.0"
__all__ = ["MarkdownRedactor", "RedactionConfig"]
