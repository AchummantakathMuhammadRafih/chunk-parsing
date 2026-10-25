"""Audio & Video Transcription Module with Timestamped Outputs."""

__version__ = "1.0.0"

from media_transcriber.core.transcriber import MediaTranscriber
from media_transcriber.models.schemas import TranscriptionResult, SegmentInfo

__all__ = ["MediaTranscriber", "TranscriptionResult", "SegmentInfo"]
