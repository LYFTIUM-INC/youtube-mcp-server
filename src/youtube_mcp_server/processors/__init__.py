"""
Video and audio processing modules for advanced trimming operations.

This module provides high-performance processors for:
- Video trimming and manipulation using MoviePy and FFmpeg
- Audio extraction and processing using Pydub
- Format conversion and optimization
- Batch processing capabilities
"""

from .video_processor import VideoProcessor, TrimOperation
from .audio_processor import AudioProcessor, AudioSegment

__all__ = [
    "VideoProcessor",
    "TrimOperation",
    "AudioProcessor", 
    "AudioSegment"
]