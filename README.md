# Media Transcriber

A completely independent, modular Python package, CLI, and Web UI for transcribing audio and video files (`.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, etc.) into text with accurate timestamps.

Powered by **OpenAI Whisper**, **FFmpeg**, and **PyTorch (CUDA GPU Acceleration)**.

---

## Features

- **Timestamped Transcriptions**:
  - `[00:01 -> 00:05] Transcribed text` human-readable text format (`.txt`)
  - Subtitle formats: SubRip (`.srt`) and WebVTT (`.vtt`)
  - Structured formats: JSON (`.json`) with start/end seconds and metadata, Tab-Separated Values (`.tsv`)
- **Format Support**: Handles `.mp3`, `.mp4`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.mkv`, `.mov`, `.webm`, etc.
- **GPU Acceleration**: Supports NVIDIA CUDA for **10x–40x faster transcription** compared to CPU.
- **Interactive Web UI**: Upload multiple media files, choose models, select hardware acceleration, and process jobs asynchronously in a background thread with real-time status updates and file downloads.
- **Word-Level Timestamps**: Optional word-by-word timing (`--word-timestamps`).
- **Translation**: Translates non-English media directly into English transcripts (`--translate`).
- **Batch Processing**: Transcribe whole directories at once (`batch` command).
- **Rich Terminal UI**: Pretty tables, banners, and status spinners.

---

## Available Whisper Models

| Model | Parameters | Relative Speed | VRAM Required | Recommended Device | Best For |
|---|---|---|---|---|---|
| **tiny** | 39 M | ~32x | ~1 GB | CPU / GPU | Ultra-fast drafting |
| **base** | 74 M | ~16x | ~1 GB | CPU / GPU | General purpose (Default) |
| **small** | 244 M | ~6x | ~2 GB | GPU / Fast CPU | Balanced speed & accuracy |
| **medium** | 769 M | ~2x | ~5 GB | GPU (CUDA) | High-accuracy transcription |
| **large** | 1550 M | 1x | ~10 GB | GPU (CUDA) | Maximum multilingual accuracy |
| **large-v3** | 1550 M | 1x | ~10 GB | GPU (CUDA) | Latest Whisper state-of-the-art |

---

## Installation & Setup

Ensure **FFmpeg** is installed and accessible in your system PATH.

### 1. Clone & Setup Environment
```bash
# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
```

### 2. GPU Acceleration Setup (NVIDIA CUDA)
For 10x–40x speedups, install PyTorch with CUDA support:

```bash
# NVIDIA CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU-only machines:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

Verify GPU availability:
```bash
python -c "import torch; print('CUDA Available:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### 3. Install Package
```bash
pip install openai-whisper gradio
pip install -e .
```

---

## Web UI (Studio)

Launch the interactive Web UI with file uploads, model picker, GPU/CPU selector, and background worker queue:

```bash
media-transcriber ui
# or
python -m media_transcriber.ui
```

Then open your browser to **http://127.0.0.1:7860**.

### UI Flags:
```bash
# Bind to all interfaces (for remote VM access):
media-transcriber ui --host 0.0.0.0 --port 7860

# Generate a temporary public shareable Gradio link:
media-transcriber ui --share
```

---

## CLI Usage

### Transcribing Single Files
```bash
# Transcribe with default model (base) and auto-device
media-transcriber transcribe path/to/recording.mp3

# Transcribe with GPU acceleration and small model
media-transcriber transcribe podcast.mp3 -m small -d cuda

# Transcribe video directly to output folder
media-transcriber transcribe lecture.mp4 -o output/transcriptions

# Transcribe and translate foreign language audio to English
media-transcriber transcribe interview.m4a --translate

# Transcribe with word-level timestamps
media-transcriber transcribe speech.wav --word-timestamps

# Export only SRT subtitle format
media-transcriber transcribe video.mp4 -f srt
```

### Batch Directory Transcription
```bash
# Batch transcribe an entire directory with GPU acceleration
media-transcriber batch input/recordings/ -o output/transcriptions -m medium -d cuda

# Batch transcribe recursively into subdirectories
media-transcriber batch input/recordings/ -r
```

---

## Remote VM Deployment Guide (Ubuntu / Debian / EC2 / GCP)

### 1. Install System Packages & FFmpeg
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg git
```

### 2. Verify NVIDIA Drivers (For GPU instances)
```bash
nvidia-smi
```

### 3. Clone, Install, and Run
```bash
git clone <repo_url> app
cd app
python3 -m venv .venv
source .venv/bin/activate

# Install CUDA PyTorch & Dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install openai-whisper gradio
pip install -e .

# Launch bound to 0.0.0.0
media-transcriber ui --host 0.0.0.0 --port 7860
```

### 4. Run as Background Systemd Service
Create `/etc/systemd/system/transcriber.service`:
```ini
[Unit]
Description=Media Transcriber Studio Web UI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app
ExecStart=/home/ubuntu/app/.venv/bin/media-transcriber ui --host 0.0.0.0 --port 7860
Restart=always
RestartSec=5
Environment=PATH=/home/ubuntu/app/.venv/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
```
Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now transcriber
```

---

## Python API Usage

```python
from pathlib import Path
from media_transcriber import MediaTranscriber
from media_transcriber.exporters import TranscriptionWriter

# Load transcriber with GPU acceleration
transcriber = MediaTranscriber(model_name="small", device="cuda")

# Run transcription
result = transcriber.transcribe(
    file_path=Path("recording.mp3"),
    task="transcribe",
    word_timestamps=True
)

# Access timestamped segments
for segment in result.segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s]: {segment.text}")

# Export all file formats (txt, raw.txt, srt, vtt, json, tsv)
TranscriptionWriter.export_all(result, Path("output/transcriptions"), "recording")
```
