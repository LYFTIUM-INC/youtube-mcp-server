"""
YouTube Analytics MCP Server

A Model Context Protocol server for YouTube analytics and data collection.
"""

__version__ = "0.1.0"
__author__ = "YouTube MCP Team"
__description__ = "YouTube Analytics MCP Server"

# Core imports
from .core.config import YouTubeMCPConfig, Config
from .core.exceptions import (
    YouTubeMCPError,
    YouTubeAPIError,
    QuotaExceededError,
    ValidationError,
)

# Tools
from .tools.core_tools import YouTubeMCPTools
from .tools.youtube_api_client import YouTubeAPIClient
from .tools.video_downloader import VideoDownloader

# Infrastructure
from .infrastructure.cache_manager import CacheManager, ErrorHandler
from .infrastructure.rate_limiter import RateLimiter
from .infrastructure.retry_manager import RetryManager

__all__ = [
    # Core
    "YouTubeMCPConfig",
    "Config",
    
    # Exceptions
    "YouTubeMCPError",
    "YouTubeAPIError", 
    "QuotaExceededError",
    "ValidationError",
    
    # Tools
    "YouTubeMCPTools",
    "YouTubeAPIClient",
    "VideoDownloader",
    
    # Infrastructure
    "CacheManager",
    "RateLimiter",
    "RetryManager",
    "ErrorHandler",
]

def get_version() -> str:
    """Get the current version of the package."""
    return __version__