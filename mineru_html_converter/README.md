# MinerU Document to HTML Converter

A standalone CLI tool and Python module for converting PDF, Word (`.docx`, `.doc`), PowerPoint (`.pptx`, `.ppt`), and Excel (`.xlsx`, `.xls`, `.csv`, `.tsv`) documents into semantic, responsive HTML powered by the **MinerU** document layout engine.

---

## Highlights

1. **Multi-Format Document Support**:
   - Seamlessly converts **PDF**, **DOCX**, **PPTX**, and **XLSX** documents with exact formatting, table structures, and headings.
2. **Native MinerU Document Parser**:
   - Accurately identifies headings, paragraphs, lists, tables, code blocks, math equations, and figures.
3. **Self-Contained Portable HTML**:
   - Automatically embeds extracted images as inline base64 data URIs (`--embed-images`), yielding a single portable `.html` file with zero external file dependencies.
4. **Responsive Presentation & Themes**:
   - Injects modern CSS typography with 4 built-in themes: `modern` (default), `dark`, `readable` (editorial book style), and `minimal`.
5. **Interactive Floating Table of Contents**:
   - Automatically builds an anchor-linked Table of Contents sidebar for easy document navigation (`--toc`).
6. **Flexible Page Range & Batch Processing**:
   - Convert specific page ranges (e.g. `-p "1-5"`) or batch process entire folders of mixed documents.

---

## Installation

The CLI commands are registered directly via `setup.py`:

```bash
pip install -e .
```

---

## CLI Usage

### Convert a Document (PDF, DOCX, PPTX, XLSX)

```bash
# Convert a PDF
mineru-html convert document.pdf -o output/report.html

# Convert a Word document (.docx)
mineru-html convert report.docx -o output/report.html

# Convert a PowerPoint presentation (.pptx)
mineru-html convert presentation.pptx -o output/presentation.html

# Convert an Excel spreadsheet (.xlsx)
mineru-html convert data.xlsx -o output/data.html

# Or use python module invocation
python -m mineru_html_converter convert document.docx

# Apply a dark theme with custom title
mineru-html convert document.docx -t dark --title "System Architecture"

# Use full page-break container layout
mineru-html convert document.pdf -m full
```

### Batch Conversion

Convert all documents within a directory:

```bash
mineru-html batch input/documents -o output/html_reports -t modern
```

---

## Available Options

| Option | Flag | Description | Default |
|---|---|---|---|
| `--output` | `-o` | Target HTML path or directory | `output/html/<stem>.html` |
| `--pages` | `-p` | Page range to convert (`'1-5'`, `'all'`) | All pages |
| `--mode` | `-m` | Render layout mode (`default`, `full`) | `default` |
| `--theme` | `-t` | Visual theme (`modern`, `dark`, `readable`, `minimal`) | `modern` |
| `--embed-images / --no-embed-images` | | Inlines extracted images as base64 | `True` |
| `--toc / --no-toc` | | Floating Table of Contents navigation | `True` |
| `--title` | | Custom document title | Document stem |
| `--verbose` | `-v` | Enable detailed debug logs | `False` |

---

## Python API Usage

```python
from pathlib import Path
from mineru_html_converter import MinerUHTMLConverter, HTMLConversionConfig

# 1. Initialize converter with configuration
config = HTMLConversionConfig(
    pages="1-5",
    theme="modern",
    embed_images=True,
    add_toc=True
)
converter = MinerUHTMLConverter(config=config)

# 2. Convert PDF to HTML
result = converter.convert(
    input_path=Path("document.pdf"),
    output_path=Path("output/document.html")
)

if result.success:
    print(f"HTML created: {result.output_html_file} ({result.file_size_bytes} bytes)")
    print(f"Images embedded: {result.embedded_images_count}")
else:
    print(f"Conversion failed: {result.error_message}")
```
