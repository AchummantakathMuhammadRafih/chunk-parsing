"""Tests for Markdown PII Redactor."""

from pathlib import Path
import pytest
from markdown_redactor import MarkdownRedactor, RedactionConfig


def test_markdown_redactor_basic():
    config = RedactionConfig(score_threshold=0.4, mask_char="*")
    redactor = MarkdownRedactor(config=config)

    sample = "Please write to John Doe at john.doe@example.com."
    redacted, findings, counts = redactor.redact_text(sample)

    assert "john.doe@example.com" not in redacted
    assert "John Doe" not in redacted
    assert "*" in redacted
    assert len(findings) >= 2


def test_markdown_code_preservation():
    config = RedactionConfig(ignore_code_blocks=True, mask_char="*")
    redactor = MarkdownRedactor(config=config)

    sample = (
        "Here is text about Jane Smith.\n\n"
        "```python\n"
        'email = "dev@internal.corp"\n'
        "```\n"
    )
    redacted, findings, counts = redactor.redact_text(sample)

    # In-text name should be redacted
    assert "Jane Smith" not in redacted
    # In-code content should remain intact
    assert 'email = "dev@internal.corp"' in redacted


def test_markdown_image_url_preservation():
    config = RedactionConfig(ignore_image_urls=True, mask_char="*")
    redactor = MarkdownRedactor(config=config)

    sample = (
        "Author: Robert Frost\n"
        "![Diagram](/api/v1/documents/images/raw?blobPath=images%2Fdefault%2Fsample.png)"
    )
    redacted, findings, counts = redactor.redact_text(sample)

    assert "Robert Frost" not in redacted
    assert "![]" in redacted or "![Diagram]" in redacted
    assert "/api/v1/documents/images/raw?blobPath=" in redacted


def test_redact_file(tmp_path: Path):
    config = RedactionConfig(score_threshold=0.4)
    redactor = MarkdownRedactor(config=config)

    test_md = tmp_path / "test.md"
    test_md.write_text("Call Alice at 555-123-4567 in London.", encoding="utf-8")

    out_md = tmp_path / "test.redacted.md"
    result = redactor.redact_file(test_md, out_md)

    assert result.success is True
    assert result.findings_count > 0
    assert out_md.exists()
    content = out_md.read_text(encoding="utf-8")
    assert "555-123-4567" not in content
