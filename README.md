# Media Transcriber

A completely independent, modular Python package and CLI for transcribing audio and video files (`.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, etc.) into text with accurate timestamps.

Powered by OpenAI Whisper and FFmpeg.

---

## Features

- **Timestamped Transcriptions**:
  - `[00:01 -> 00:05] Transcribed text` human-readable text format (`.txt`)
  - Subtitle formats: SubRip (`.srt`) and WebVTT (`.vtt`)
  - Structured formats: JSON (`.json`) with start/end seconds and metadata, Tab-Separated Values (`.tsv`)
- **Format Support**: Handles `.mp3`, `.mp4`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.mkv`, `.mov`, `.webm`, etc.
- **Word-Level Timestamps**: Optional word-by-word timing (`--word-timestamps`).
- **Translation**: Translates non-English media directly into English transcripts (`--translate`).
- **Batch Processing**: Transcribe whole directories at once (`batch` command).
- **Rich Terminal UI**: Pretty tables, banners, and status spinners.

---

## Installation & Requirements

Ensure FFmpeg is installed and accessible in your PATH.

Dependencies:
- `openai-whisper`
- `click`
- `rich`
- `pydantic`
- `torch`

---

## CLI Usage

Run directly as a Python module:

```bash
# Transcribe a single MP3 or MP4 file (generates txt, raw.txt, srt, vtt, json, tsv)
python -m media_transcriber transcribe path/to/recording.mp3

# Transcribe an MP4 video file to a specific output folder
python -m media_transcriber transcribe lecture.mp4 -o output/transcriptions

# Transcribe with a specific model size (tiny, base, small, medium, large, large-v3)
python -m media_transcriber transcribe podcast.mp3 -m small

# Transcribe only as SRT subtitle format
python -m media_transcriber transcribe video.mp4 -f srt

# Batch transcribe an entire folder of MP3/MP4 files
python -m media_transcriber batch input/recordings -o output/batch_transcriptions
```

---

## Python API Usage

```python
from pathlib import Path
from media_transcriber import MediaTranscriber
from media_transcriber.exporters import TranscriptionWriter

transcriber = MediaTranscriber(model_name="base")
result = transcriber.transcribe(Path("audio.mp3"))

# Print timestamped segments
for segment in result.segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s]: {segment.text}")

# Export to all formats
TranscriptionWriter.export_all(result, Path("output/transcriptions"), "audio")
```
