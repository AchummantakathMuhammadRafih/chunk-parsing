"""Pydantic data models for media transcription."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WordInfo(BaseModel):
    """Timestamped word data."""
    word: str
    start: float
    end: float
    probability: Optional[float] = None


class SegmentInfo(BaseModel):
    """Transcription segment with precise start and end timestamps."""
    id: int
    seek: Optional[int] = 0
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Segment transcription text")
    tokens: Optional[List[int]] = None
    temperature: Optional[float] = None
    avg_logprob: Optional[float] = None
    compression_ratio: Optional[float] = None
    no_speech_prob: Optional[float] = None
    words: Optional[List[WordInfo]] = None


class TranscriptionResult(BaseModel):
    """Overall transcription result."""
    source_file: str
    media_type: str
    duration_seconds: Optional[float] = None
    language: str
    language_probability: Optional[float] = None
    text: str
    segments: List[SegmentInfo] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
