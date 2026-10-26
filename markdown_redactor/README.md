# Markdown PII Redactor 🛡️✨

A modular, production-grade CLI toolkit and Python framework for redacting Personally Identifiable Information (**PII**) from **Markdown (`.md`, `.markdown`)** documents using **Microsoft Presidio** (`presidio-analyzer` & `presidio-anonymizer`) with asterisk (`*`) star-masking.

---

## 🌟 Key Features

- **Accurate PII Detection via Presidio**: Detects names, email addresses, phone numbers, locations, street addresses, credit cards, SSNs, IP addresses, and bank details.
- **Asterisk Star-Masking**: Replaces sensitive data with exact-length or full star masks (e.g. `John Doe` -> `********`, `john@corp.com` -> `*************`).
- **Markdown-Aware Preservation**:
  - Automatically isolates and protects code blocks (` ```...``` `) and inline code (`` `code` ``) from false-positive redaction.
  - Automatically protects Markdown image tags and asset URL paths (`![](/path/to/img.png)`).
- **Custom Enhancements**: Custom street address pattern recognizer for catching residential addresses.
- **Rich Terminal UI**: Formatted tables, entity frequency breakdowns, and execution summaries powered by `rich`.
- **Batch Directory Processing**: Recursively process entire directories or documentation trees with summary reporting.

---

## 🚀 CLI Quick Start

### 1. View Supported Entities
```bash
markdown-redact entities
```

### 2. Redact a Single Markdown File
```bash
# Writes to <filename>.redacted.md by default
markdown-redact redact input/document.md

# Specify custom output path
markdown-redact redact input/document.md -o output/sanitized.md

# Specify custom threshold and custom masking character
markdown-redact redact input/document.md -t 0.5 -m "*"

# Redact specific entities only
markdown-redact redact input/document.md -e PERSON -e EMAIL_ADDRESS
```

### 3. Batch Redact a Directory
```bash
# Redact all markdown files in a directory recursively
markdown-redact batch output/results -o output/redacted_results
```

---

## 💻 Python Library Usage

```python
from markdown_redactor import MarkdownRedactor, RedactionConfig

# 1. Configure redactor
config = RedactionConfig(
    score_threshold=0.4,
    mask_char="*",
    ignore_code_blocks=True,
    ignore_image_urls=True,
)
redactor = MarkdownRedactor(config=config)

# 2. Redact in-memory text
text = "Contact Alice Smith at alice@example.com or 555-123-4567. She lives at 123 Main Street."
redacted, findings, counts = redactor.redact_text(text)
print(redacted)
# Output: Contact *********** at ***************** or ************. She lives at ***************.

# 3. Redact a file
result = redactor.redact_file("document.md", "document.redacted.md")
print(f"Redacted {result.findings_count} entities in {result.execution_time:.2f}s")
```
