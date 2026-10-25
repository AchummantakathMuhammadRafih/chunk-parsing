"""Core transcription engine using OpenAI Whisper with timestamps."""

from pathlib import Path
from typing import Optional, Dict, Any, List
import whisper
import torch

from media_transcriber.models.schemas import TranscriptionResult, SegmentInfo, WordInfo
from media_transcriber.utils.audio_utils import get_media_type, is_supported_media
from media_transcriber.utils.logging_utils import setup_logger

logger = setup_logger("media_transcriber.core")


class MediaTranscriber:
    """Handles loading Whisper model and running transcription on audio/video files."""

    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        self.model_name = model_name
        if device is None or device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Loading Whisper model '{self.model_name}' on device '{self.device}'...")
        self.model = whisper.load_model(self.model_name, device=self.device)
        logger.info(f"Whisper model '{self.model_name}' loaded successfully.")

    def transcribe(
        self,
        file_path: Path,
        language: Optional[str] = None,
        task: str = "transcribe",
        word_timestamps: bool = False,
        temperature: float = 0.0,
        initial_prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio or video file to text with segment timestamps.
        
        Args:
            file_path: Path to MP3, MP4, WAV, etc.
            language: Language code (e.g., 'en', 'es', 'fr') or None for auto-detect.
            task: 'transcribe' or 'translate' (translates to English).
            word_timestamps: Whether to extract word-level timestamps.
            temperature: Sampling temperature.
            initial_prompt: Optional initial prompt for context.
        """
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")
        if not is_supported_media(file_path):
            raise ValueError(f"Unsupported media file format: {file_path.suffix}")

        media_type = get_media_type(file_path)
        logger.info(f"Starting transcription of {media_type.upper()}: {file_path.name}")

        transcribe_args: Dict[str, Any] = {
            "task": task,
            "temperature": temperature,
            "word_timestamps": word_timestamps,
            "verbose": False,
        }
        if language:
            transcribe_args["language"] = language
        if initial_prompt:
            transcribe_args["initial_prompt"] = initial_prompt

        raw_result = self.model.transcribe(str(file_path), **transcribe_args)

        detected_language = raw_result.get("language", language or "unknown")
        full_text = raw_result.get("text", "").strip()

        segments: List[SegmentInfo] = []
        for s in raw_result.get("segments", []):
            words_list: Optional[List[WordInfo]] = None
            if word_timestamps and "words" in s:
                words_list = [
                    WordInfo(
                        word=w.get("word", ""),
                        start=w.get("start", 0.0),
                        end=w.get("end", 0.0),
                        probability=w.get("probability"),
                    )
                    for w in s.get("words", [])
                ]

            seg = SegmentInfo(
                id=s.get("id", 0),
                seek=s.get("seek", 0),
                start=round(float(s.get("start", 0.0)), 3),
                end=round(float(s.get("end", 0.0)), 3),
                text=s.get("text", "").strip(),
                tokens=s.get("tokens"),
                temperature=s.get("temperature"),
                avg_logprob=s.get("avg_logprob"),
                compression_ratio=s.get("compression_ratio"),
                no_speech_prob=s.get("no_speech_prob"),
                words=words_list,
            )
            segments.append(seg)

        duration = segments[-1].end if segments else 0.0

        return TranscriptionResult(
            source_file=str(file_path),
            media_type=media_type,
            duration_seconds=duration,
            language=detected_language,
            text=full_text,
            segments=segments,
            metadata={
                "model": self.model_name,
                "device": self.device,
                "task": task,
                "word_timestamps": word_timestamps,
            },
        )
