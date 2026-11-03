"""Web UI for Media Transcriber with file upload, model selection, device (GPU/CPU) selection, and background thread processing."""

import os
import shutil
import queue
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import gradio as gr
import torch

from media_transcriber.core.transcriber import MediaTranscriber
from media_transcriber.exporters.writers import TranscriptionWriter
from media_transcriber.config.settings import WhisperModelSize
from media_transcriber.utils.audio_utils import format_timestamp_short


# Global state & caches
MODEL_CACHE: Dict[str, MediaTranscriber] = {}
MODEL_CACHE_LOCK = threading.Lock()

# Job store: job_id -> dict with details
JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()

# Task Queue for Background Processing Thread
TASK_QUEUE: queue.Queue = queue.Queue()

# Default upload & output directories
UI_UPLOAD_DIR = Path("output/ui_uploads")
UI_RESULTS_DIR = Path("output/ui_transcriptions")
UI_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
UI_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OPTIONS = [
    ("tiny - Fastest, lowest memory (~39M params)", "tiny"),
    ("base - Fast, general-purpose (~74M params, Default)", "base"),
    ("small - Balanced speed and high accuracy (~244M params)", "small"),
    ("medium - High accuracy (~769M params)", "medium"),
    ("large - Maximum accuracy (~1550M params)", "large"),
    ("large-v3 - Latest Whisper state-of-the-art model", "large-v3"),
]


def detect_device_info() -> Dict[str, Any]:
    """Detect GPU / CUDA status and details."""
    has_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if has_cuda else "CPU"
    device_count = torch.cuda.device_count() if has_cuda else 0
    return {
        "has_cuda": has_cuda,
        "device_name": device_name,
        "device_count": device_count,
        "default_device": "cuda" if has_cuda else "cpu",
    }


def get_cached_transcriber(model_name: str, device: str = "auto") -> MediaTranscriber:
    """Load or retrieve Whisper model instance cached in memory."""
    key = f"{model_name}_{device}"
    with MODEL_CACHE_LOCK:
        if key not in MODEL_CACHE:
            MODEL_CACHE[key] = MediaTranscriber(model_name=model_name, device=device)
        return MODEL_CACHE[key]


def worker_loop():
    """Background thread consuming transcription tasks from the queue."""
    while True:
        task = TASK_QUEUE.get()
        if task is None:
            break

        job_id = task["job_id"]
        file_path = task["file_path"]
        model_name = task["model_name"]
        device = task.get("device", "auto")
        language = task["language"]
        task_mode = task["task_mode"]
        word_timestamps = task["word_timestamps"]
        output_format = task["output_format"]

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "Processing"
            JOBS[job_id]["started_at"] = datetime.now().strftime("%H:%M:%S")

        try:
            transcriber = get_cached_transcriber(model_name=model_name, device=device)
            result = transcriber.transcribe(
                file_path=file_path,
                language=language if language and language.strip() else None,
                task=task_mode,
                word_timestamps=word_timestamps,
            )

            # Export outputs
            stem = file_path.stem
            job_out_dir = UI_RESULTS_DIR / job_id
            job_out_dir.mkdir(parents=True, exist_ok=True)

            txt_path = job_out_dir / f"{stem}.txt"
            raw_txt_path = job_out_dir / f"{stem}.raw.txt"
            srt_path = job_out_dir / f"{stem}.srt"
            vtt_path = job_out_dir / f"{stem}.vtt"
            json_path = job_out_dir / f"{stem}.json"
            tsv_path = job_out_dir / f"{stem}.tsv"

            TranscriptionWriter.write_txt_with_timestamps(result, txt_path)
            TranscriptionWriter.write_plain_text(result, raw_txt_path)
            TranscriptionWriter.write_srt(result, srt_path)
            TranscriptionWriter.write_vtt(result, vtt_path)
            TranscriptionWriter.write_json(result, json_path)
            TranscriptionWriter.write_tsv(result, tsv_path)

            formatted_txt = txt_path.read_text(encoding="utf-8")

            with JOBS_LOCK:
                JOBS[job_id]["status"] = "Completed"
                JOBS[job_id]["completed_at"] = datetime.now().strftime("%H:%M:%S")
                JOBS[job_id]["detected_language"] = result.language
                JOBS[job_id]["duration"] = format_timestamp_short(result.duration_seconds or 0.0)
                JOBS[job_id]["raw_text"] = result.full_text
                JOBS[job_id]["timestamped_text"] = formatted_txt
                JOBS[job_id]["device_used"] = getattr(transcriber, "device", device)
                JOBS[job_id]["download_files"] = [
                    str(txt_path),
                    str(raw_txt_path),
                    str(srt_path),
                    str(vtt_path),
                    str(json_path),
                    str(tsv_path),
                ]

        except Exception as exc:
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "Failed"
                JOBS[job_id]["error"] = str(exc)
        finally:
            TASK_QUEUE.task_done()


# Start background worker daemon thread
WORKER_THREAD = threading.Thread(target=worker_loop, daemon=True)
WORKER_THREAD.start()


def submit_transcription_jobs(
    files: List[Any],
    model_name: str,
    device_choice: str,
    language: str,
    task_mode: str,
    word_timestamps: bool,
    output_format: str,
):
    """Enqueues uploaded files into the background thread pool."""
    if not files:
        return "⚠️ Please upload at least one media file (.mp3, .mp4, .wav, .m4a, etc.)."

    queued_count = 0
    for f in files:
        file_path_src = Path(f.name if hasattr(f, "name") else str(f))
        job_id = str(uuid.uuid4())[:8]

        # Copy file to managed workspace directory
        saved_file_path = UI_UPLOAD_DIR / f"{job_id}_{file_path_src.name}"
        shutil.copy2(file_path_src, saved_file_path)

        with JOBS_LOCK:
            JOBS[job_id] = {
                "job_id": job_id,
                "file_name": file_path_src.name,
                "file_path": saved_file_path,
                "model_name": model_name,
                "device": device_choice,
                "status": "Queued",
                "submitted_at": datetime.now().strftime("%H:%M:%S"),
                "started_at": "-",
                "completed_at": "-",
                "detected_language": "-",
                "duration": "-",
                "raw_text": "",
                "timestamped_text": "",
                "download_files": [],
                "error": None,
            }

        task = {
            "job_id": job_id,
            "file_path": saved_file_path,
            "model_name": model_name,
            "device": device_choice,
            "language": language,
            "task_mode": task_mode,
            "word_timestamps": word_timestamps,
            "output_format": output_format,
        }
        TASK_QUEUE.put(task)
        queued_count += 1

    return f"✅ Enqueued {queued_count} file(s) for background processing."


def get_job_table_data():
    """Returns a list of rows for the Job Status Table."""
    with JOBS_LOCK:
        rows = []
        for jid, info in reversed(list(JOBS.items())):
            status_display = info["status"]
            if info["status"] == "Processing":
                status_display = "⏳ Processing"
            elif info["status"] == "Completed":
                status_display = "✅ Completed"
            elif info["status"] == "Queued":
                status_display = "🕒 Queued"
            elif info["status"] == "Failed":
                status_display = "❌ Failed"

            dev_disp = info.get("device_used", info.get("device", "auto")).upper()

            rows.append([
                info["job_id"],
                info["file_name"],
                info["model_name"],
                dev_disp,
                status_display,
                info.get("detected_language", "-"),
                info.get("duration", "-"),
                info["submitted_at"],
                info.get("completed_at", "-"),
            ])
        return rows


def get_job_choices():
    """Dropdown list of job IDs for viewing details."""
    with JOBS_LOCK:
        choices = []
        for jid, info in reversed(list(JOBS.items())):
            choices.append(f"{jid} - {info['file_name']} ({info['status']})")
        return choices


def view_job_details(selected_choice: Optional[str]):
    """Returns the details and files for a selected job."""
    if not selected_choice:
        return "", "", None, ""

    job_id = selected_choice.split(" - ")[0].strip()
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return "", "", None, "Job not found"

        error_msg = f"Error: {job['error']}" if job.get("error") else ""
        return (
            job.get("timestamped_text", ""),
            job.get("raw_text", ""),
            job.get("download_files", None),
            error_msg,
        )


def create_app() -> gr.Blocks:
    """Constructs and returns the Gradio application."""
    dev_info = detect_device_info()
    has_gpu = dev_info["has_cuda"]
    device_banner = (
        f"⚡ **GPU Acceleration Active:** `{dev_info['device_name']}` ({dev_info['device_count']} GPU found)"
        if has_gpu
        else "💻 **Hardware Info:** Running on CPU (No CUDA GPU detected on current host)"
    )

    custom_css = """
    .gradio-container { max-width: 1200px !important; margin: 0 auto !important; }
    """

    with gr.Blocks(title="Media Transcriber Studio", css=custom_css, theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            f"""
            # 🎙️ Media Transcriber Studio
            ### High-speed speech-to-text with Whisper & background thread queuing.
            
            > {device_banner}
            """
        )

        with gr.Row():
            # Left column: Upload & Parameters
            with gr.Column(scale=1):
                gr.Markdown("### 1. Upload Media")
                file_input = gr.File(
                    label="Audio / Video Files",
                    file_count="multiple",
                    file_types=["audio", "video", ".mp3", ".mp4", ".wav", ".m4a", ".mkv", ".webm", ".flac", ".ogg"],
                )

                gr.Markdown("### 2. Model & Acceleration")
                model_dropdown = gr.Dropdown(
                    label="Model Size",
                    choices=[opt[1] for opt in MODEL_OPTIONS],
                    value="base",
                    info="tiny/base for speed; small/medium/large for highest accuracy.",
                )

                device_radio = gr.Radio(
                    label="Compute Device (GPU Acceleration)",
                    choices=[
                        ("Auto-detect (Prefers CUDA GPU if available)", "auto"),
                        ("NVIDIA CUDA (GPU)", "cuda"),
                        ("CPU", "cpu"),
                    ],
                    value="cuda" if has_gpu else "auto",
                    info="Select 'cuda' for GPU acceleration if an NVIDIA card is available."
                )

                with gr.Accordion("Model Details & Specifications", open=False):
                    gr.Markdown(
                        """
                        | Model | Parameters | Relative Speed | VRAM Required | Speedup on GPU |
                        |---|---|---|---|---|
                        | **tiny** | 39 M | ~32x | ~1 GB | ~10-20x vs CPU |
                        | **base** | 74 M | ~16x | ~1 GB | ~10-20x vs CPU |
                        | **small** | 244 M | ~6x | ~2 GB | ~15-25x vs CPU |
                        | **medium** | 769 M | ~2x | ~5 GB | ~20-30x vs CPU |
                        | **large** | 1550 M | 1x | ~10 GB | ~25-40x vs CPU |
                        | **large-v3**| 1550 M | 1x | ~10 GB | ~25-40x vs CPU |
                        """
                    )

                with gr.Accordion("Advanced Options", open=False):
                    lang_input = gr.Textbox(
                        label="Language (Optional)",
                        placeholder="e.g. en, es, fr, de, hi (Leave blank for auto-detect)",
                    )
                    task_radio = gr.Radio(
                        label="Task",
                        choices=[("Transcribe original audio", "transcribe"), ("Translate to English", "translate")],
                        value="transcribe",
                    )
                    word_timestamps_check = gr.Checkbox(
                        label="Generate Word-Level Timestamps",
                        value=False,
                    )
                    format_dropdown = gr.Dropdown(
                        label="Output Format",
                        choices=["all", "txt", "srt", "vtt", "json", "tsv"],
                        value="all",
                    )

                submit_btn = gr.Button("🚀 Submit to Processing Queue", variant="primary", size="lg")
                submission_status = gr.Markdown()

            # Right column: Queue & Live Progress
            with gr.Column(scale=2):
                gr.Markdown("### 3. Background Queue & Tasks")
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh Status", size="sm")

                job_table = gr.Dataframe(
                    headers=["Job ID", "File Name", "Model", "Device", "Status", "Lang", "Duration", "Queued At", "Done At"],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str", "str"],
                    value=get_job_table_data,
                    interactive=False,
                )

                gr.Markdown("### 4. Results & Exports")
                job_selector = gr.Dropdown(
                    label="Select Completed Job",
                    choices=get_job_choices(),
                    interactive=True,
                )

                with gr.Tabs():
                    with gr.TabItem("🕒 Timestamped Transcript"):
                        timestamped_output = gr.TextArea(
                            label="Timestamped Text ([MM:SS -> MM:SS])",
                            lines=12,
                            interactive=False,
                        )
                    with gr.TabItem("📝 Raw Text"):
                        raw_output = gr.TextArea(
                            label="Full Raw Transcript",
                            lines=12,
                            interactive=False,
                        )
                    with gr.TabItem("💾 Download Files"):
                        file_downloads = gr.File(
                            label="Exported Files (.txt, .srt, .vtt, .json, .tsv)",
                            file_count="multiple",
                            interactive=False,
                        )

                error_display = gr.Markdown()

        # Interactivity wiring
        def on_submit(*args):
            status = submit_transcription_jobs(*args)
            return status, get_job_table_data(), gr.update(choices=get_job_choices())

        submit_btn.click(
            fn=on_submit,
            inputs=[
                file_input,
                model_dropdown,
                device_radio,
                lang_input,
                task_radio,
                word_timestamps_check,
                format_dropdown,
            ],
            outputs=[submission_status, job_table, job_selector],
        )

        def on_refresh():
            return get_job_table_data(), gr.update(choices=get_job_choices())

        refresh_btn.click(
            fn=on_refresh,
            inputs=[],
            outputs=[job_table, job_selector],
        )

        job_selector.change(
            fn=view_job_details,
            inputs=[job_selector],
            outputs=[timestamped_output, raw_output, file_downloads, error_display],
        )

        # Automatic periodic refresh every 3 seconds
        timer = gr.Timer(value=3.0)
        timer.tick(
            fn=on_refresh,
            inputs=[],
            outputs=[job_table, job_selector],
        )

    return demo


def launch(host: str = "127.0.0.1", port: int = 7860, share: bool = False):
    """Launch the Web UI."""
    demo = create_app()
    demo.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    launch()
