"""
Video Frame Extraction Tool for YouTube MCP Server.
Extracts frames from videos using ffmpeg for detailed analysis.
"""

import os
import logging
import subprocess
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from ..core.config import YouTubeMCPConfig
from ..infrastructure.cache_manager import CacheManager, RateLimiter, ErrorHandler
from ..core.exceptions import (
    DownloadError,
    VideoNotFoundError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class FrameExtractionConfig:
    """Configuration for frame extraction."""
    
    def __init__(
        self,
        segment_start: Optional[Union[int, str]] = None,
        segment_end: Optional[Union[int, str]] = None,
        interval_seconds: float = 1.0,
        max_frames: int = 100,
        output_format: str = "jpg",
        quality: str = "high",
        resolution: Optional[str] = None
    ):
        """
        Initialize frame extraction configuration.
        
        Args:
            segment_start: Start time (seconds from beginning, or "end-X" for X seconds from end)
            segment_end: End time (seconds from beginning, or "end-X" for X seconds from end)
            interval_seconds: Time between extracted frames
            max_frames: Maximum number of frames to extract
            output_format: Image format (jpg, png, bmp)
            quality: Quality setting (high, medium, low)
            resolution: Output resolution (e.g., "1920x1080", "1280x720")
        """
        self.segment_start = segment_start
        self.segment_end = segment_end
        self.interval_seconds = max(0.1, interval_seconds)  # Minimum 0.1 seconds
        self.max_frames = min(1000, max(1, max_frames))  # Between 1 and 1000 frames
        self.output_format = output_format.lower()
        self.quality = quality.lower()
        self.resolution = resolution


class VideoFrameExtractor:
    """Extract frames from videos using ffmpeg."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the frame extractor.
        
        Args:
            cache_manager: Cache manager for storing results
        """
        self.logger = logging.getLogger(__name__)
        self.cache = cache_manager or CacheManager()
        
        # Check if ffmpeg is available
        self._check_ffmpeg_available()
        
        # Create output directory
        self.frames_dir = Path("output/frames")
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Add output_dir property for compatibility
        self.output_dir = self.frames_dir
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on the system."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info("ffmpeg is available")
                return True
            else:
                raise ConfigurationError("ffmpeg is not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise ConfigurationError(f"ffmpeg is not available on the system: {e}")
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DownloadError(f"ffprobe failed: {stderr.decode()}")
            
            info = json.loads(stdout.decode())
            
            # Extract video stream info
            video_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise DownloadError("No video stream found in file")
            
            duration = float(info.get("format", {}).get("duration", 0))
            
            return {
                "duration": duration,
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": eval(video_stream.get("avg_frame_rate", "0/1")),  # Convert fraction to float
                "codec": video_stream.get("codec_name", "unknown"),
                "bitrate": int(info.get("format", {}).get("bit_rate", 0)),
                "size": int(info.get("format", {}).get("size", 0))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get video info: {e}")
            raise DownloadError(f"Failed to analyze video: {e}")
    
    def _parse_time_specification(self, time_spec: Union[int, str, None], duration: float, is_end: bool = False) -> Optional[float]:
        """
        Parse time specification into seconds.
        
        Args:
            time_spec: Time specification (seconds, "end-X", or None)
            duration: Total video duration
            is_end: Whether this is for end time (affects default behavior)
            
        Returns:
            Time in seconds, or None if not specified
        """
        if time_spec is None:
            return duration if is_end else 0.0
        
        if isinstance(time_spec, (int, float)):
            return max(0, min(float(time_spec), duration))
        
        if isinstance(time_spec, str):
            # Handle "end-X" format
            if time_spec.startswith("end-"):
                try:
                    offset = float(time_spec[4:])
                    return max(0, duration - offset)
                except ValueError:
                    self.logger.warning(f"Invalid time specification: {time_spec}")
                    return duration if is_end else 0.0
            
            # Handle time format like "MM:SS" or "HH:MM:SS"
            if ":" in time_spec:
                try:
                    parts = time_spec.split(":")
                    if len(parts) == 2:  # MM:SS
                        minutes, seconds = parts
                        return float(minutes) * 60 + float(seconds)
                    elif len(parts) == 3:  # HH:MM:SS
                        hours, minutes, seconds = parts
                        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                except ValueError:
                    pass
            
            # Try parsing as number
            try:
                return max(0, min(float(time_spec), duration))
            except ValueError:
                self.logger.warning(f"Invalid time specification: {time_spec}")
                return duration if is_end else 0.0
        
        return duration if is_end else 0.0
    
    async def extract_frames(
        self,
        video_path: str,
        config: FrameExtractionConfig,
        output_prefix: str = "frame"
    ) -> Dict[str, Any]:
        """
        Extract frames from video using ffmpeg.
        
        Args:
            video_path: Path to the input video
            config: Frame extraction configuration
            output_prefix: Prefix for output frame files
            
        Returns:
            Dictionary with extraction results
        """
        start_time = time.time()
        
        try:
            # Get video information
            video_info = await self.get_video_info(video_path)
            duration = video_info["duration"]
            
            self.logger.info(f"Video duration: {duration:.2f} seconds")
            
            # Parse time specifications
            start_seconds = self._parse_time_specification(config.segment_start, duration, False)
            end_seconds = self._parse_time_specification(config.segment_end, duration, True)
            
            # Ensure valid time range
            if start_seconds >= end_seconds:
                raise ValueError(f"Invalid time range: start ({start_seconds}) >= end ({end_seconds})")
            
            segment_duration = end_seconds - start_seconds
            
            # Calculate number of frames
            max_possible_frames = int(segment_duration / config.interval_seconds) + 1
            actual_frames = min(config.max_frames, max_possible_frames)
            
            # Create output directory for this extraction
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.frames_dir / f"{output_prefix}_{timestamp}"
            output_dir.mkdir(exist_ok=True)
            
            # Build ffmpeg command
            output_pattern = str(output_dir / f"{output_prefix}_%04d.{config.output_format}")
            
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-ss", str(start_seconds),  # Start time
                "-t", str(segment_duration),  # Duration
                "-vf", f"fps=1/{config.interval_seconds}",  # Frame rate filter
                "-frames:v", str(actual_frames),  # Limit number of frames
            ]
            
            # Add quality settings
            if config.output_format == "jpg":
                if config.quality == "high":
                    cmd.extend(["-q:v", "2"])  # High quality JPEG
                elif config.quality == "medium":
                    cmd.extend(["-q:v", "5"])  # Medium quality
                else:
                    cmd.extend(["-q:v", "8"])  # Lower quality
            
            # Add resolution if specified
            if config.resolution:
                cmd.extend(["-s", config.resolution])
            
            # Add output pattern
            cmd.append(output_pattern)
            
            # Overwrite existing files
            cmd.append("-y")
            
            self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
            
            # Run ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
                self.logger.error(f"ffmpeg failed: {error_msg}")
                raise DownloadError(f"Frame extraction failed: {error_msg}")
            
            # List extracted frames
            extracted_frames = list(output_dir.glob(f"{output_prefix}_*.{config.output_format}"))
            extracted_frames.sort()
            
            # Calculate frame timestamps
            frame_info = []
            for i, frame_path in enumerate(extracted_frames):
                frame_time = start_seconds + (i * config.interval_seconds)
                frame_info.append({
                    "frame_number": i + 1,
                    "file_path": str(frame_path),
                    "timestamp": frame_time,
                    "time_formatted": f"{int(frame_time // 60):02d}:{int(frame_time % 60):02d}.{int((frame_time % 1) * 100):02d}",
                    "file_size": frame_path.stat().st_size if frame_path.exists() else 0
                })
            
            extraction_time = time.time() - start_time
            
            result = {
                "success": True,
                "video_info": video_info,
                "extraction_config": {
                    "segment_start": start_seconds,
                    "segment_end": end_seconds,
                    "segment_duration": segment_duration,
                    "interval_seconds": config.interval_seconds,
                    "max_frames": config.max_frames,
                    "output_format": config.output_format,
                    "quality": config.quality,
                    "resolution": config.resolution
                },
                "frames": frame_info,
                "output_directory": str(output_dir),
                "total_frames": len(extracted_frames),
                "extraction_time": extraction_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Successfully extracted {len(extracted_frames)} frames in {extraction_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Frame extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_frames(self, older_than_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old frame extraction directories.
        
        Args:
            older_than_hours: Remove directories older than this many hours
            
        Returns:
            Cleanup results
        """
        try:
            cutoff_time = time.time() - (older_than_hours * 3600)
            deleted_dirs = []
            deleted_files = 0
            freed_space = 0
            
            for item in self.frames_dir.iterdir():
                if item.is_dir():
                    # Check directory modification time
                    if item.stat().st_mtime < cutoff_time:
                        # Count files and calculate size before deletion
                        dir_files = 0
                        dir_size = 0
                        for file_path in item.rglob("*"):
                            if file_path.is_file():
                                dir_files += 1
                                dir_size += file_path.stat().st_size
                        
                        # Delete directory
                        shutil.rmtree(item)
                        deleted_dirs.append(str(item))
                        deleted_files += dir_files
                        freed_space += dir_size
            
            return {
                "success": True,
                "deleted_directories": len(deleted_dirs),
                "deleted_files": deleted_files,
                "freed_space_bytes": freed_space,
                "freed_space_mb": round(freed_space / (1024 * 1024), 2),
                "directories": deleted_dirs,
                "older_than_hours": older_than_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Frame cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }