"""
Advanced video and audio analysis models for YouTube MCP Server.

This module provides AI-powered models for:
- Video scene detection and analysis
- Audio pattern recognition and classification
- Computer vision-based content understanding
- Speech and environmental sound recognition
"""

from .video_models import VideoAnalyzer, SceneDetector
from .audio_models import AudioAnalyzer, SoundClassifier, WhisperTranscriber

__all__ = [
    "VideoAnalyzer",
    "SceneDetector", 
    "AudioAnalyzer",
    "SoundClassifier",
    "WhisperTranscriber"
]