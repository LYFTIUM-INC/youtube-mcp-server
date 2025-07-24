"""
Video downloader for MCP server integration.

Adapted from the existing media_operations_reliable.py implementation with MCP-specific enhancements.
"""

import os
import logging
import time
import random
import subprocess
import json
import tempfile
import shutil
import asyncio
from typing import Optional, Dict, Any, List, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
import yt_dlp
import requests
from dataclasses import dataclass
from enum import Enum

from ..core.config import Config
from ..infrastructure.cache_manager import CacheManager, RateLimiter, RetryManager, ErrorHandler
from ..core.exceptions import (
    DownloadError,
    VideoNotFoundError,
    ConfigurationError
)


class DownloadFormat(Enum):
    """Supported download formats."""
    BEST = "best"
    BEST_VIDEO = "bestvideo"
    BEST_AUDIO = "bestaudio"
    MP4_720P = "best[ext=mp4][height<=720]"
    MP4_1080P = "best[ext=mp4][height<=1080]"
    MP3_AUDIO = "bestaudio[ext=m4a]/bestaudio/best"
    WEBM_VIDEO = "best[ext=webm]"


class DownloadQuality(Enum):
    """Download quality presets."""
    HIGHEST = "best"
    HIGH = "best[height<=1080]"
    MEDIUM = "best[height<=720]"
    LOW = "best[height<=480]"
    AUDIO_ONLY = "bestaudio"


@dataclass(frozen=True)
class DownloadOptions:
    """Download configuration options."""
    format: Union[DownloadFormat, str] = DownloadFormat.BEST
    quality: Optional[DownloadQuality] = None
    include_subtitles: bool = False
    include_thumbnail: bool = False
    include_metadata: bool = True
    output_directory: Optional[str] = None
    filename_template: Optional[str] = None
    extract_audio: bool = False
    audio_format: str = "mp3"
    
    def __post_init__(self):
        """Convert format to string for hashability."""
        if isinstance(self.format, DownloadFormat):
            object.__setattr__(self, 'format', self.format.value)
        if isinstance(self.quality, DownloadQuality):
            object.__setattr__(self, 'quality', self.quality.value)


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    video_id: str
    title: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    error_message: Optional[str] = None
    download_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class VideoDownloader:
    """
    Reliable video downloader with multiple fallback strategies.
    
    Adapted from existing media_operations_reliable.py with MCP server enhancements.
    """
    
    def __init__(self, cache_manager=None, rate_limiter=None, error_handler=None, download_dir: str = "downloads"):
        """
        Initialize the video downloader.
        
        Args:
            cache_manager: Cache manager instance
            rate_limiter: Rate limiter instance
            error_handler: Error handler instance
            download_dir: Directory for downloaded files
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(download_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided components or create defaults
        self.cache = cache_manager or CacheManager(cache_dir="download_cache", ttl_seconds=1800)
        self.rate_limiter = rate_limiter or RateLimiter(tokens_per_second=0.2, bucket_size=3)
        self.error_handler = error_handler
        self.retry_manager = RetryManager(
            max_retries=3,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=2.0
        )
        
        # Track download statistics
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'last_success': None,
            'last_failure': None,
            'total_size': 0,
            'total_time': 0.0
        }
        
        # Rate limiting
        self.last_download_time = None
        self.min_interval = 5.0  # Minimum seconds between downloads
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
        ]
        
        # Update yt-dlp on initialization
        self._update_ytdlp()
        
        self.logger.info("VideoDownloader initialized successfully")
    
    def _update_ytdlp(self):
        """Update yt-dlp to the latest version."""
        try:
            self.logger.info("Checking yt-dlp version...")
            result = subprocess.run(
                ["pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self.logger.info("yt-dlp updated successfully")
            else:
                self.logger.warning(f"Failed to update yt-dlp: {result.stderr}")
        except Exception as e:
            self.logger.warning(f"Could not update yt-dlp: {e}")
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between downloads."""
        await self.rate_limiter.acquire()
        
        if self.last_download_time:
            elapsed = time.time() - self.last_download_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed + random.uniform(0.5, 2.0)
                self.logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
        self.last_download_time = time.time()
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.user_agents)
    
    def _get_base_ydl_opts(self, options: DownloadOptions) -> Dict[str, Any]:
        """Get base yt-dlp options with 2025 best practices."""
        # Determine output directory
        output_dir = Path(options.output_directory) if options.output_directory else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine format
        format_selector = options.format.value if isinstance(options.format, DownloadFormat) else options.format
        if options.quality:
            format_selector = options.quality.value
        
        # Add fallback for format selection to handle restricted videos
        if format_selector and "height" in str(format_selector):
            # For height-based selectors, add fallback to any available format
            format_selector = f"{format_selector}/best/worst"
        
        # Filename template
        filename_template = options.filename_template or '%(title)s-%(id)s.%(ext)s'
        
        opts = {
            # Output template
            'outtmpl': str(output_dir / filename_template),
            
            # Logging
            'quiet': True,
            'no_warnings': True,
            'logger': self.logger,
            
            # User agent rotation
            'user_agent': self._get_random_user_agent(),
            
            # Minimal headers to avoid bot detection
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            
            # Network settings
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            
            # Format selection
            'format': format_selector,
            
            # Age gate handling
            'age_limit': None,
            
            # Add extractor args for better compatibility
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Skip problematic formats
                    'player_skip': ['js'],    # Skip JavaScript player
                }
            },
            
            # Subtitles
            'writesubtitles': options.include_subtitles,
            'writeautomaticsub': options.include_subtitles,
            'subtitleslangs': ['en'],
            
            # Thumbnail
            'writethumbnail': options.include_thumbnail,
            
            # Metadata
            'writeinfojson': options.include_metadata,
            
            # Progress
            'progress_hooks': [self._progress_hook],
            
            # No check certificate (helps with some network issues)
            'nocheckcertificate': True,
            
            # Extract flat (for testing)
            'extract_flat': False,
            
            # Geo bypass (disabled to avoid detection)
            # 'geo_bypass': True,
            # 'geo_bypass_country': 'US',
            
            # Post-processing for audio extraction
            'postprocessors': []
        }
        
        # Add audio extraction post-processor if requested
        if options.extract_audio:
            opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.audio_format,
                'preferredquality': '192',
            })
        
        return opts
    
    def _progress_hook(self, d: Dict[str, Any]):
        """Progress hook for download monitoring."""
        if d['status'] == 'downloading':
            if 'total_bytes' in d and 'downloaded_bytes' in d:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                self.logger.debug(f"Progress: {percent:.1f}%")
        elif d['status'] == 'finished':
            self.logger.info(f"Download finished: {d.get('filename', 'unknown')}")
    
    async def _try_direct_download(self, url: str, options: DownloadOptions) -> Optional[Dict[str, Any]]:
        """Try direct download with basic options."""
        try:
            self.logger.info("Trying direct download...")
            opts = self._get_base_ydl_opts(options)
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _download)
            
            if info:
                self.logger.info("Direct download successful!")
                return info
        except Exception as e:
            self.logger.debug(f"Direct download failed: {e}")
        
        return None
    
    async def _try_with_cookies(self, url: str, options: DownloadOptions) -> Optional[Dict[str, Any]]:
        """Try downloading with fresh browser cookies (Linux-compatible)."""
        import platform
        
        # Skip cookie strategy on Linux where browser cookies are often inaccessible
        if platform.system().lower() == 'linux':
            self.logger.debug("Skipping browser cookies strategy on Linux")
            return None
            
        browsers = ['firefox', 'chrome', 'chromium', 'edge', 'safari']
        
        for browser in browsers:
            try:
                self.logger.info(f"Trying with {browser} cookies...")
                opts = self._get_base_ydl_opts(options)
                opts['cookiesfrombrowser'] = (browser,)
                
                def _download():
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        return ydl.extract_info(url, download=True)
                
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, _download)
                
                if info:
                    self.logger.info(f"Success with {browser} cookies!")
                    return info
            except Exception as e:
                self.logger.debug(f"Failed with {browser} cookies: {e}")
                continue
        
        return None
    
    async def _try_with_android_client(self, url: str, options: DownloadOptions) -> Optional[Dict[str, Any]]:
        """Try using Android client API."""
        try:
            self.logger.info("Trying with Android client...")
            opts = self._get_base_ydl_opts(options)
            opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android'],
                    'player_skip': ['webpage', 'configs'],
                }
            }
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _download)
            
            if info:
                self.logger.info("Success with Android client!")
                return info
        except Exception as e:
            self.logger.debug(f"Android client failed: {e}")
        
        return None
    
    async def _try_with_ios_client(self, url: str, options: DownloadOptions) -> Optional[Dict[str, Any]]:
        """Try using iOS client API."""
        try:
            self.logger.info("Trying with iOS client...")
            opts = self._get_base_ydl_opts(options)
            opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['ios'],
                    'player_skip': ['webpage'],
                }
            }
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _download)
            
            if info:
                self.logger.info("Success with iOS client!")
                return info
        except Exception as e:
            self.logger.debug(f"iOS client failed: {e}")
        
        return None
    
    async def _try_with_web_client(self, url: str, options: DownloadOptions) -> Optional[Dict[str, Any]]:
        """Try using web client with simplified options."""
        try:
            self.logger.info("Trying with simplified web client...")
            opts = self._get_base_ydl_opts(options)
            
            # Simplify format selection for problematic videos
            opts['format'] = 'best/worst'  # Very permissive format selection
            opts['ignoreerrors'] = True
            opts['no_check_certificate'] = True
            
            # Remove problematic extractor args
            if 'extractor_args' in opts:
                del opts['extractor_args']
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _download)
            
            if info:
                self.logger.info("Success with simplified web client!")
                return info
        except Exception as e:
            self.logger.debug(f"Simplified web client failed: {e}")
        
        return None
    
    async def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        import re
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume it's already a video ID
        if len(url) == 11 and url.isalnum():
            return url
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    async def download_video(
        self, 
        video_id: str,
        quality: str = "best",
        format_preference: str = "mp4",
        audio_only: bool = False,
        include_subtitles: bool = False,
        subtitle_languages: List[str] = None,
        url: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> Dict[str, Any]:
        """
        Download a video with multiple fallback strategies.
        
        Args:
            url: YouTube URL or video ID
            options: Download configuration options
            
        Returns:
            DownloadResult with download information
        """
        if subtitle_languages is None:
            subtitle_languages = ["en"]
            
        # Create options from parameters if not provided
        if options is None:
            # Map quality strings to proper format selectors
            quality_map = {
                "best": DownloadFormat.BEST,
                "worst": "worst",
                "720p": "best[height<=720]",
                "480p": "best[height<=480]", 
                "360p": "best[height<=360]",
                "240p": "best[height<=240]"
            }
            
            format_selector = quality_map.get(quality, DownloadFormat.BEST)
            
            options = DownloadOptions(
                format=format_selector,
                extract_audio=audio_only,
                include_subtitles=include_subtitles,
                output_directory=str(self.output_dir)
            )
        
        start_time = time.time()
        
        # Use provided URL or construct from video_id
        if url is None:
            url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            video_id = await self._extract_video_id(url)
        
        # Check cache first (for metadata)
        cache_key = f"download_meta_{video_id}"
        cached_result = await self.cache.get(cache_key)
        
        # Enforce rate limiting
        await self._enforce_rate_limit()
        
        self.stats['attempts'] += 1
        
        # Ensure URL is complete
        if not url.startswith('http'):
            url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Try different download strategies (ordered by success likelihood)
        strategies = [
            ("Direct Download", self._try_direct_download),
            ("iOS Client", self._try_with_ios_client),
            ("Simplified Web Client", self._try_with_web_client),
            ("Android Client", self._try_with_android_client),
            ("Browser Cookies", self._try_with_cookies),
        ]
        
        download_info = None
        last_error = None
        strategy_errors = []
        
        for strategy_name, strategy_func in strategies:
            try:
                self.logger.info(f"Attempting strategy: {strategy_name}")
                download_info = await strategy_func(url, options)
                if download_info:
                    self.logger.info(f"Strategy '{strategy_name}' succeeded!")
                    break
                else:
                    error_msg = f"Strategy '{strategy_name}' returned no data"
                    strategy_errors.append(error_msg)
                    last_error = error_msg
                    self.logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Strategy '{strategy_name}' failed: {str(e)}"
                strategy_errors.append(error_msg)
                last_error = str(e)
                self.logger.warning(error_msg)
                continue
        
        if not download_info:
            self.stats['failures'] += 1
            self.stats['last_failure'] = datetime.now().isoformat()
            
            # Create detailed error message
            strategy_summary = "; ".join(strategy_errors) if strategy_errors else "No detailed errors available"
            error_msg = f"All {len(strategies)} download strategies failed for video {video_id}. Details: {strategy_summary}"
            self.logger.error(error_msg)
            
            result = DownloadResult(
                success=False,
                video_id=video_id,
                title="Unknown",
                error_message=error_msg,
                download_time=time.time() - start_time
            )
            return result.__dict__
        
        # Process successful download
        try:
            download_time = time.time() - start_time
            
            # Extract file information
            file_path = None
            file_size = None
            
            if 'requested_downloads' in download_info and download_info['requested_downloads']:
                file_path = download_info['requested_downloads'][0].get('filepath')
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
            
            # Create result
            result = DownloadResult(
                success=True,
                video_id=video_id,
                title=download_info.get('title', 'Unknown'),
                file_path=file_path,
                file_size=file_size,
                duration=download_info.get('duration'),
                format=download_info.get('format'),
                download_time=download_time,
                metadata={
                    'uploader': download_info.get('uploader'),
                    'upload_date': download_info.get('upload_date'),
                    'view_count': download_info.get('view_count'),
                    'like_count': download_info.get('like_count'),
                    'description': download_info.get('description', '')[:500],  # Truncate description
                }
            )
            
            # Update statistics
            self.stats['successes'] += 1
            self.stats['last_success'] = datetime.now().isoformat()
            if file_size:
                self.stats['total_size'] += file_size
            self.stats['total_time'] += download_time
            
            # Cache metadata
            await self.cache.set(cache_key, result.__dict__)
            
            self.logger.info(f"Successfully downloaded: {result.title} ({video_id})")
            return result.__dict__
            
        except Exception as e:
            self.stats['failures'] += 1
            self.stats['last_failure'] = datetime.now().isoformat()
            error_msg = f"Failed to process download result: {e}"
            self.logger.error(error_msg)
            
            result = DownloadResult(
                success=False,
                video_id=video_id,
                title=download_info.get('title', 'Unknown'),
                error_message=error_msg,
                download_time=time.time() - start_time
            )
            return result.__dict__
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Extract video information without downloading.
        
        Args:
            url: YouTube URL or video ID
            
        Returns:
            Video information dictionary
        """
        video_id = await self._extract_video_id(url)
        cache_key = f"info_{video_id}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Ensure URL is complete
        if not url.startswith('http'):
            url = f"https://www.youtube.com/watch?v={video_id}"
        
        async def _extract_info():
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'user_agent': self._get_random_user_agent(),
            }
            
            def _extract():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _extract)
        
        try:
            info = await self.retry_manager.execute_with_retry(_extract_info)
            
            # Cache the result
            await self.cache.set(cache_key, info)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to extract video info for {url}: {e}")
            raise DownloadError(f"Failed to extract video info: {e}")
    
    async def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """
        Get available download formats for a video.
        
        Args:
            url: YouTube URL or video ID
            
        Returns:
            List of available formats
        """
        info = await self.get_video_info(url)
        formats = info.get('formats', [])
        
        # Filter and clean format information
        cleaned_formats = []
        for fmt in formats:
            cleaned_format = {
                'format_id': fmt.get('format_id'),
                'ext': fmt.get('ext'),
                'resolution': fmt.get('resolution'),
                'fps': fmt.get('fps'),
                'vcodec': fmt.get('vcodec'),
                'acodec': fmt.get('acodec'),
                'filesize': fmt.get('filesize'),
                'quality': fmt.get('quality'),
            }
            cleaned_formats.append(cleaned_format)
        
        return cleaned_formats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats['attempts'] > 0:
            stats['success_rate'] = stats['successes'] / stats['attempts']
        else:
            stats['success_rate'] = 0.0
        
        if stats['successes'] > 0:
            stats['avg_download_time'] = stats['total_time'] / stats['successes']
            stats['avg_file_size'] = stats['total_size'] / stats['successes']
        else:
            stats['avg_download_time'] = 0.0
            stats['avg_file_size'] = 0
        
        return stats
    
    async def get_download_formats(self, video_id: str) -> Dict[str, Any]:
        """
        Get available download formats for a video (wrapper for get_available_formats).
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with available formats information
        """
        try:
            # Construct URL from video_id
            url = f"https://www.youtube.com/watch?v={video_id}"
            formats = await self.get_available_formats(url)
            
            return {
                "video_id": video_id,
                "success": True,
                "formats": formats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get formats for video {video_id}: {e}")
            return {
                "video_id": video_id,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup_downloads(self, older_than_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old downloaded files.
        
        Args:
            older_than_hours: Delete files older than this many hours
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            import time
            import glob
            
            cutoff_time = time.time() - (older_than_hours * 3600)
            deleted_files = []
            deleted_size = 0
            
            # Find all files in download directory
            pattern = str(self.output_dir / "**" / "*")
            for file_path in glob.glob(pattern, recursive=True):
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    if file_stat.st_mtime < cutoff_time:
                        file_size = file_stat.st_size
                        try:
                            os.remove(file_path)
                            deleted_files.append({
                                "path": file_path,
                                "size": file_size,
                                "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                            })
                            deleted_size += file_size
                        except Exception as e:
                            self.logger.warning(f"Could not delete {file_path}: {e}")
            
            self.logger.info(f"Cleaned up {len(deleted_files)} files, freed {deleted_size} bytes")
            
            return {
                "success": True,
                "deleted_files_count": len(deleted_files),
                "deleted_files": deleted_files,
                "total_size_freed": deleted_size,
                "older_than_hours": older_than_hours,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }