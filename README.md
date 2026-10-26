# MinerU Document Conversion & HTML Toolkit 📄⚡

A modular, production-grade CLI suite and Python framework for high-fidelity document parsing, artifact extraction, and HTML generation using **MinerU** (`magic-pdf`).

Supports **PDF**, **Microsoft Word (`.docx`, `.doc`)**, **PowerPoint (`.pptx`, `.ppt`)**, **Excel (`.xlsx`, `.xls`, `.csv`, `.tsv`)**, and **Audio/Video Transcription**.

---

## 🌟 Key Features

- **Multi-Engine Document Parsing**:
  - Full MinerU extraction suite for PDFs (Markdown, Content Lists V1/V2, Layout JSON, Model ASTs, Annotated visual PDFs).
  - Native conversion of **PDF, DOCX, PPTX, and XLSX** into standalone, responsive HTML with base64 embedded assets and themes.
  - 📝 **Markdown (`.md`)**: Clean, formatted text with LaTeX math and image markdown links.
  - 📋 **V1 Content List (`_content_list.json` / `_v1list.json`)**: Flat block-level element stream.
  - 📊 **V2 Content List (`_content_list_v2.json` / `_v2list.json`)**: Rich hierarchical block stream with bounding boxes and metadata.
  - 🌳 **Middle AST JSON (`_middle.json`)**: Full document layout analysis intermediate tree.
  - 🤖 **Model JSON (`_model.json`)**: Raw neural network layout/OCR/table detection outputs.
  - 🖼️ **Visual Bounding Box Overlays**:
    - `_layout.pdf`: Color-coded block layout bounding boxes.
    - `_span.pdf`: Fine-grained inline token/span bounding boxes.
  - 📑 **Original Slice (`_origin.pdf`)**: Normalized PDF source for the processed page range.
  - 🎨 **Extracted Media (`images/`)**: High-res extracted diagrams, tables, equations, and photo figures.
  - 🧾 **Conversion Manifest (`conversion_manifest.json`)**: Checksums, file paths, and execution metadata.
  - 📈 **Document Summary (`conversion_summary.json`)**: Word counts, character counts, tables, formulas, and timing stats.

- **Modular Architecture**: Built following clean architectural principles with separated config, models, core engines, exporters, and CLI layers.
- **Multiple Backends**:
  - `pipeline`: Robust local hybrid pipeline (DocLayout, OCR, Table Cls/Rec, Unimernet).
  - `hybrid-engine`: High-accuracy local VLM + layout engine.
  - `vlm-engine`: Pure vision-language model inference.
  - `hybrid-http-client` / `vlm-http-client`: Connect to remote MinerU API / OpenAI-compatible servers.
- **Rich Terminal UI**: Beautiful banners, colored tables, progress indicators, and artifact status tables powered by `rich`.
- **Batch Processing**: Recursively convert entire directories of PDFs with progress tracking and failure isolation.
- **Python Library API**: Use directly within your Python applications as an importable module.

---

## 🏗️ Project Structure

```
chunk_parsing/
├── mineru_converter/               # Core PDF Conversion Package
│   ├── __init__.py                 # Root exports & public API
│   ├── __main__.py                 # Entrypoint for `python -m mineru_converter`
│   ├── config/                     # Configuration management
│   ├── models/                     # Data contracts and schemas
│   ├── core/                       # Core engine orchestrators
│   ├── exporters/                  # Output file formatters & manifest builders
│   ├── utils/                      # Shared utilities
│   └── cli/                        # Click CLI commands (convert, batch, inspect, info)
│
├── mineru_html_converter/          # PDF to Semantic HTML Converter Package
│   ├── __init__.py                 # Public API (MinerUHTMLConverter, HTMLConversionConfig)
│   ├── __main__.py                 # Entrypoint for `python -m mineru_html_converter`
│   ├── cli/                        # CLI commands (convert, batch) & formatters
│   ├── config/                     # Settings, themes & render modes
│   ├── core/                       # MinerU HTML converter engine
│   ├── exporters/                  # Postprocessor (base64 image inlining, TOC, themes)
│   ├── models/                     # HTML conversion result schemas
│   └── utils/                      # Path utils & logging
│
├── media_transcriber/              # Speech-to-Text Transcription Package
│   ├── __init__.py                 # Public API (MediaTranscriber)
│   ├── __main__.py                 # Entrypoint for `python -m media_transcriber`
│   ├── cli/                        # CLI commands (transcribe, batch) & formatters
│   ├── config/                     # Settings, model sizes & format enums
│   ├── core/                       # Whisper transcription engine
│   ├── exporters/                  # Writers for txt, srt, vtt, json, tsv
│   ├── models/                     # Transcription segment & result dataclasses
│   └── utils/                      # Audio format detection & logging
│
├── markdown_redactor/              # Markdown PII Redaction & Star-Masking Package
│   ├── __init__.py                 # Public API (MarkdownRedactor, RedactionConfig)
│   ├── __main__.py                 # Entrypoint for `python -m markdown_redactor`
│   ├── cli/                        # CLI commands (redact, batch, entities) & formatters
│   ├── config/                     # Settings & entity constants
│   ├── core/                       # Presidio Analyzer & Anonymizer engine
│   ├── models/                     # Finding & RedactionResult dataclasses
│   └── utils/                      # File search & logging utils
│
├── tests/                          # Test suite
│   ├── test_converter.py           # Unit & integration tests
│   └── test_html_converter.py      # HTML converter unit tests
├── cli.py                          # Top-level CLI launcher
├── setup.py                        # Package setup & console scripts
└── pyproject.toml                  # Build configuration
```

---

## 🚀 CLI Quick Start

### 1. Single PDF Conversion
Convert a PDF and generate all output artifacts:
```bash
# Using installed console script
mineru-convert convert input/document.pdf -o output/results

# Or using cli.py
python cli.py convert input/document.pdf -o output/results
```

### 2. Page Range Selection
Process only a specific page range (0-indexed, inclusive):
```bash
# Convert only the first 3 pages (pages 0, 1, 2)
mineru-convert convert input/document.pdf -s 0 -e 2 -o output/results
```

### 3. Backend & Parsing Mode
Choose backend engine and parsing mode:
```bash
# Use fast text-extraction mode for clean digital PDFs
mineru-convert convert input/document.pdf -m txt

# Force OCR mode for scanned documents
mineru-convert convert input/document.pdf -m ocr -l ch
```

### 4. Batch Directory Conversion
Convert all PDFs in a directory recursively:
```bash
mineru-convert batch ./input -o ./output/batch_results
```

### 5. Inspect Converted Output
Inspect and review artifacts generated for a document:
```bash
mineru-convert inspect output/results/document/auto
```

### 6. Intermediate Step: Re-chunk Directly from Markdown (`chunk`)
If you already have MinerU outputs (Markdown, content list, and extracted images) and only want to re-run the Docling hybrid chunking step without re-parsing the PDF:
```bash
# Point to an output directory containing .md and _content_list.json
mineru-convert chunk output/results/Panasonic_HD_Camera_User_Manual/auto

# Or point directly to a Markdown file
mineru-convert chunk output/results/Panasonic_HD_Camera_User_Manual/auto/Panasonic_HD_Camera_User_Manual.md

# Specify custom chunking options or a different output folder
mineru-convert chunk path/to/doc.md -o path/to/output --docling-max-tokens 512
```

### 7. Environment & GPU Info
Display installed MinerU versions, CUDA devices, and model paths:
```bash
mineru-convert info
```

---

## 💻 Python Library Usage

You can seamlessly import `mineru_converter` into any Python script or pipeline:

```python
from pathlib import Path
from mineru_converter import MinerUConverter, ConversionConfig, BackendType, ParseMethod

# 1. Configure the conversion pipeline
config = ConversionConfig(
    output_dir=Path("./output/my_docs"),
    backend=BackendType.PIPELINE,
    method=ParseMethod.AUTO,
    formula_enable=True,
    table_enable=True,
    start_page=0,
    end_page=5,  # Process first 6 pages
    generate_manifest=True,
)

# 2. Instantiate converter
converter = MinerUConverter(config=config)

# 3. Execute conversion
result = converter.convert("input/sample.pdf")

# 4. Access output files and stats
if result.success:
    manifest = result.manifest
    stats = result.stats
    
    print(f"Markdown path: {manifest.markdown_path}")
    print(f"Content List V1: {manifest.content_list_v1_path}")
    print(f"Content List V2: {manifest.content_list_v2_path}")
    print(f"Middle AST JSON: {manifest.middle_json_path}")
    print(f"Layout PDF: {manifest.layout_pdf_path}")
    print(f"Images extracted: {len(manifest.image_files)}")
    print(f"Total Words: {stats.word_count:,}")
    print(f"Total Tables: {stats.table_count}")
    print(f"Total Formulas: {stats.formula_count}")
else:
    print(f"Conversion failed: {result.error_message}")
```

### Batch Conversion via Python:
```python
pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
summary = converter.convert_batch(pdf_files, stop_on_error=False)

print(f"Batch completed: {summary.succeeded_count}/{summary.total_documents} succeeded")
print(f"Total duration: {summary.total_duration_seconds:.2f}s")
```

---

## 📖 Output Artifact Reference

When converting `MyDocument.pdf`, the output folder contains:

| Artifact | File Name | Description |
|---|---|---|
| **Markdown** | `MyDocument.md` | Clean GitHub-flavored Markdown with equations formatted in LaTeX (`$...$`, `$$...$$`) and image references. |
| **Content List V1** | `MyDocument_content_list.json` | Stream of page items (text, table, equation, image) compatible with MinerU v1 integrations. |
| **Content List V2** | `MyDocument_content_list_v2.json` | Detailed structured stream with bounding boxes, font attributes, table cells, and caption relationships. |
| **Middle AST** | `MyDocument_middle.json` | The intermediate document AST produced by MinerU layout analysis, containing block positions, spans, and raw OCR text. |
| **Model Output** | `MyDocument_model.json` | Raw output from layout detection models (YOLO/PP-DocLayout, Unimernet, etc.). |
| **Layout Visual** | `MyDocument_layout.pdf` | Visual PDF with highlighted bounding boxes for layout blocks (Title, Text, Table, Figure). |
| **Span Visual** | `MyDocument_span.pdf` | Visual PDF highlighting individual inline text token spans and characters. |
| **Origin PDF** | `MyDocument_origin.pdf` | Normalized original document slice for the selected page range. |
| **Images** | `images/` | Directory containing all extracted crop images, diagrams, photos, formula renderings, and table snapshots. |
| **Manifest** | `conversion_manifest.json` | Index of all generated files with SHA256 checksums, byte sizes, and timestamps. |
| **Summary** | `conversion_summary.json` | High-level metrics: character count, word count, headings, tables, formulas, and duration. |
| **Docling Chunks** | `docling_chunks.json` | Docling chunk output with personal information masked and internal chunk metadata removed. |

---

## ⚙️ CLI Options Reference

### `mineru-convert convert [OPTIONS] INPUT_PATH`

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output` | `-o` | `./output/mineru` | Output directory root |
| `--backend` | `-b` | `pipeline` | Backend engine (`pipeline`, `hybrid-engine`, `vlm-engine`, `hybrid-http-client`, `vlm-http-client`) |
| `--method` | `-m` | `auto` | Parsing mode (`auto`, `txt`, `ocr`) |
| `--lang` | `-l` | `ch` | OCR language (`ch`, `en`, `korean`, `arabic`, `devanagari`, etc.) |
| `--effort` | | `medium` | Hybrid effort level (`medium`, `high`) |
| `--start-page` | `-s` | `0` | Start page index (0-indexed) |
| `--end-page` | `-e` | `None` | End page index (0-indexed, inclusive) |
| `--no-formula` | | `False` | Disable formula extraction |
| `--no-table` | | `False` | Disable table extraction |
| `--no-layout-pdf` | | `False` | Skip generating `_layout.pdf` |
| `--no-span-pdf` | | `False` | Skip generating `_span.pdf` |
| `--no-manifest` | | `False` | Skip generating `conversion_manifest.json` |
| `--server-url` | `-u` | `None` | Endpoint for remote HTTP client backends |
| `--verbose` | `-v` | `False` | Enable debug logs |
| `--quiet` | `-q` | `False` | Suppress non-error console output |

### `mineru-convert chunk [OPTIONS] TARGET`

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output` | `-o` | `None` (same as target) | Directory to write `docling_chunks.json` |
| `--docling-url` | | `http://localhost:5001` | docling-serve base URL |
| `--docling-max-tokens` | | `1024` | Maximum tokens per chunk |
| `--docling-tokenizer` | | `BAAI/bge-m3` | HuggingFace tokenizer for the chunker |
| `--docling-timeout` | | `300` | docling-serve request timeout (seconds) |

---

## 🎙️ Media Transcriber (`media-transcribe`)

The project includes `media_transcriber`, an audio/video speech-to-text transcription module powered by OpenAI Whisper and FFmpeg. It extracts timestamps for every spoken segment and exports formatted text, subtitles, and structured data.

### Supported File Formats
`.mp3`, `.mp4`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.mkv`, `.mov`, `.webm`, etc.

### Running Media Transcriber

You can run it either via the CLI command `media-transcribe` (or `media-transcriber`) or via Python module execution `python -m media_transcriber`:

#### 1. Transcribe a Single File
Transcribe an audio or video file and output all formats (`.txt`, `.srt`, `.vtt`, `.json`, `.tsv`) with timestamps:
```bash
# Using installed console script
media-transcribe transcribe path/to/recording.mp3

# Or via Python module
python -m media_transcriber transcribe path/to/recording.mp3
```

#### 2. Specify Output Directory
```bash
media-transcribe transcribe lecture.mp4 -o output/transcriptions
```

#### 3. Select Whisper Model Size
Choose from `tiny`, `base` (default), `small`, `medium`, `large`, `large-v3`:
```bash
media-transcribe transcribe interview.mp3 -m small
```

#### 4. Filter Output Formats
Generate only specific formats: `txt`, `srt`, `vtt`, `json`, `tsv`, or `all` (default):
```bash
# Generate SubRip subtitles only
media-transcribe transcribe video.mp4 -f srt

# Generate timestamped text only ([00:01 -> 00:05] Hello world)
media-transcribe transcribe video.mp4 -f txt
```

#### 5. Additional Options
- **Word-level timestamps**:
  ```bash
  media-transcribe transcribe speech.mp3 --word-timestamps
  ```
- **Translate foreign language audio into English**:
  ```bash
  media-transcribe transcribe speech_es.mp3 --translate
  ```
- **Specify compute device (`auto`, `cpu`, `cuda`)**:
  ```bash
  media-transcribe transcribe meeting.wav -d cuda
  ```

#### 6. Batch Transcribe an Entire Folder
Process an entire directory of audio/video files:
```bash
# Non-recursive
media-transcribe batch input/recordings -o output/transcriptions

# Recursive scan subdirectories
media-transcribe batch input/recordings -r -o output/transcriptions
```

### Media Transcriber Python API

```python
from pathlib import Path
from media_transcriber import MediaTranscriber
from media_transcriber.exporters import TranscriptionWriter

transcriber = MediaTranscriber(model_name="base")
result = transcriber.transcribe(Path("audio.mp3"))

# Print timestamped segments
for segment in result.segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s]: {segment.text}")

# Export all formats (txt, srt, vtt, json, tsv)
TranscriptionWriter.export_all(result, Path("output/transcriptions"), "audio")
```

---

## 🌐 MinerU Document to HTML Converter (`mineru-html`)

A dedicated CLI and Python library that converts **PDF**, **DOCX**, **PPTX**, and **XLSX** documents into clean, semantic, responsive HTML powered by the MinerU engine.

### Features
- **Multi-Format Support**: Directly converts **PDF**, Microsoft Word (`.docx`, `.doc`), PowerPoint (`.pptx`, `.ppt`), and Excel (`.xlsx`, `.xls`, `.csv`, `.tsv`).
- **Semantic Structure**: Identifies headings, paragraphs, lists, tables, code blocks, and math equations.
- **Embedded Media (`--embed-images`)**: Encodes extracted figures directly as base64 data URIs into the HTML file for 100% portable, single-file documents.
- **4 Built-in Themes**: `modern` (default), `dark`, `readable` (editorial book typography), and `minimal`.
- **Interactive Floating TOC**: Injects an anchor-linked Table of Contents sidebar (`--toc`).
- **Page Slicing & Batching**: Convert specific page ranges (e.g., `-p "1-5"`) or whole folders.

### CLI Usage
```bash
# Convert a PDF document
mineru-html convert document.pdf -o output/report.html

# Convert a Word document (.docx)
mineru-html convert report.docx -o output/report.html

# Convert a PowerPoint presentation (.pptx)
mineru-html convert presentation.pptx -o output/presentation.html

# Convert an Excel spreadsheet (.xlsx)
mineru-html convert financial_data.xlsx -o output/sheet.html

# Run via module invocation
python -m mineru_html_converter convert document.docx

# Convert specific pages with dark theme
mineru-html convert document.pdf -p "1-3" --theme dark --title "Research Report"

# Batch convert a folder of mixed documents
mineru-html batch input/ -o output/html_reports/
```

### Python API Usage
```python
from mineru_html_converter import MinerUHTMLConverter, HTMLConversionConfig

converter = MinerUHTMLConverter(
    config=HTMLConversionConfig(theme="modern", embed_images=True, add_toc=True)
)
result = converter.convert("document.pdf", "output/document.html")
print(f"Generated: {result.output_html_file} ({result.embedded_images_count} images embedded)")
```

---

## 🛡️ Markdown PII Redactor (`markdown-redact`)

A dedicated CLI and Python library that detects Personally Identifiable Information (**PII**) in Markdown files and replaces sensitive tokens with **masked stars (`*`)** using **Microsoft Presidio**.

### Features
- **Presidio Privacy Anonymization**: Recognizes Person names, Email addresses, Phone numbers, Locations, Street addresses, SSNs, Credit card numbers, and IP addresses.
- **Asterisk Star Masking**: Replaces sensitive data with exact-length asterisk characters (`*`), preserving formatting structure.
- **Markdown Preservation**:
  - Automatically isolates and protects code blocks (`` ``` ``) and inline code (`` `...` ``) from false-positive entity redaction.
  - Automatically protects Markdown image syntax (`![alt](url)`) and URL references.
- **Custom Street Address Engine**: Built-in pattern recognizer for residential and commercial street addresses.
- **Rich Terminal UI**: Displays interactive summary tables, processing speeds, and breakdown of redacted entity categories.
- **Single & Batch Mode**: Redact individual `.md` files or recursively sanitize entire documentation trees.

### CLI Usage
```bash
# Redact a single markdown file (saves to <filename>.redacted.md by default)
markdown-redact redact output/document.md

# Specify custom output path
markdown-redact redact output/document.md -o output/sanitized.md

# Redact with a custom confidence threshold (0.0 - 1.0)
markdown-redact redact output/document.md -t 0.5

# Redact specific entities only
markdown-redact redact output/document.md -e PERSON -e EMAIL_ADDRESS -e PHONE_NUMBER

# Batch redact all markdown files within a folder
markdown-redact batch output/results -o output/redacted_results

# List all supported PII entity types
markdown-redact entities

# Run via module invocation
python -m markdown_redactor redact output/document.md
```

### Python API Usage
```python
from markdown_redactor import MarkdownRedactor, RedactionConfig

# Initialize redactor
config = RedactionConfig(score_threshold=0.4, mask_char="*")
redactor = MarkdownRedactor(config=config)

# Redact string content
text = "Contact Alice at alice@example.com or 555-0199 in Boston."
redacted, findings, counts = redactor.redact_text(text)
print(redacted)
# Output: Contact ***** at ***************** or ******** in ******.

# Redact file
result = redactor.redact_file("input.md", "output.md")
print(f"Redacted {result.findings_count} entities in {result.execution_time:.2f}s")
```

---

## 🧪 Running Tests

Run the test suite:
```bash
pytest tests/ -v
```


