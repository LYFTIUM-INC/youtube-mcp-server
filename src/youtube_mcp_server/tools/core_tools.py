"""
Core YouTube MCP Tools.
Implements the main MCP tools for YouTube data collection and analysis.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..core.config import YouTubeMCPConfig
from ..core.exceptions import YouTubeAPIError, ValidationError
from ..infrastructure.cache_manager import CacheManager, RateLimiter, ErrorHandler
from ..infrastructure.resource_manager import ResourceManager
from .youtube_api_client import YouTubeAPIClient
from .video_downloader import VideoDownloader
from .frame_extractor import VideoFrameExtractor, FrameExtractionConfig
from ..prompts.video_frame_analysis_prompts import VideoFrameAnalysisPrompts
from ..prompts.dashboard_prompts import dashboard_prompt_generator
# Import advanced trimming tools conditionally
try:
    from .advanced_trimming import AdvancedTrimmingOrchestrator
    ADVANCED_TRIMMING_AVAILABLE = True
except Exception as e:
    ADVANCED_TRIMMING_AVAILABLE = False
    # Create a mock class
    class AdvancedTrimmingOrchestrator:
        def __init__(self, *args, **kwargs):
            pass
        async def smart_trim_video(self, *args, **kwargs):
            return {"success": False, "error": "Advanced trimming dependencies not available"}
        async def detect_video_scenes(self, *args, **kwargs):
            return {"success": False, "error": "Advanced trimming dependencies not available"}
        async def analyze_audio_patterns(self, *args, **kwargs):
            return {"success": False, "error": "Advanced trimming dependencies not available"}
        async def extract_content_segments(self, *args, **kwargs):
            return {"success": False, "error": "Advanced trimming dependencies not available"}
        def cleanup(self):
            pass
# Import visualization tools conditionally
try:
    from .visualization_tools import YouTubeVisualizationTools
    VISUALIZATION_AVAILABLE = True
except Exception as e:
    VISUALIZATION_AVAILABLE = False
    # Create a mock class
    class YouTubeVisualizationTools:
        def __init__(self, output_dir):
            self.output_dir = output_dir
        def create_engagement_chart(self, *args, **kwargs):
            return {"success": False, "error": "Visualization dependencies not available"}
        def create_word_cloud(self, *args, **kwargs):
            return {"success": False, "error": "Visualization dependencies not available"}
        def create_performance_radar(self, *args, **kwargs):
            return {"success": False, "error": "Visualization dependencies not available"}
        def create_views_timeline(self, *args, **kwargs):
            return {"success": False, "error": "Visualization dependencies not available"}
        def create_comparison_heatmap(self, *args, **kwargs):
            return {"success": False, "error": "Visualization dependencies not available"}


logger = logging.getLogger(__name__)


class YouTubeMCPTools:
    """Core YouTube MCP Tools implementation."""
    
    def __init__(self, config: YouTubeMCPConfig):
        """Initialize YouTube MCP Tools.
        
        Args:
            config: YouTube MCP configuration
        """
        self.config = config
        cache_config = config.get_cache_config()
        rate_config = config.get_rate_limit_config()
        
        self.cache_manager = CacheManager(
            cache_dir=cache_config['cache_dir'],
            ttl_seconds=cache_config['ttl_seconds']
        )
        self.rate_limiter = RateLimiter(
            tokens_per_second=rate_config['tokens_per_second'],
            bucket_size=rate_config['bucket_size']
        )
        self.error_handler = ErrorHandler()
        self.api_client = YouTubeAPIClient(
            api_key=config.google_api_key,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter,
            error_handler=self.error_handler
        )
        self.video_downloader = VideoDownloader(
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter,
            error_handler=self.error_handler,
            download_dir=config.download_directory
        )
        self.visualization_tools = YouTubeVisualizationTools(
            output_dir=str(Path(config.output_directory) / "visualizations")
        )
        self.resource_manager = ResourceManager(
            base_path=Path(config.output_directory) / "resources"
        )
        self.frame_extractor = VideoFrameExtractor(
            cache_manager=self.cache_manager
        )
        
        # Initialize advanced trimming orchestrator if available
        if ADVANCED_TRIMMING_AVAILABLE and config.is_feature_enabled('advanced_trimming'):
            trimming_config = config.get_advanced_trimming_config()
            self.advanced_trimming = AdvancedTrimmingOrchestrator(
                cache_manager=self.cache_manager,
                error_handler=self.error_handler,
                temp_dir=Path(trimming_config['temp_processing_dir']),
                use_gpu=trimming_config['enable_gpu_acceleration']
            )
        else:
            self.advanced_trimming = AdvancedTrimmingOrchestrator()
        
    async def initialize(self) -> None:
        """Initialize all components."""
        try:
            # Cache manager doesn't need async initialization
            await self.api_client.initialize()
            logger.info("YouTube MCP Tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube MCP Tools: {e}", exc_info=True)
            raise
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        cleanup_errors = []
        
        try:
            await self.api_client.cleanup()
        except Exception as e:
            cleanup_errors.append(f"API client cleanup: {e}")
            logger.error(f"Error cleaning up API client: {e}")
        
        try:
            # Cache manager cleanup is handled automatically
            if hasattr(self, 'advanced_trimming'):
                self.advanced_trimming.cleanup()
        except Exception as e:
            cleanup_errors.append(f"Advanced trimming cleanup: {e}")
            logger.error(f"Error cleaning up advanced trimming: {e}")
        
        if cleanup_errors:
            logger.warning(f"Cleanup completed with errors: {'; '.join(cleanup_errors)}")
        else:
            logger.info("YouTube MCP Tools cleaned up successfully")
        
    def get_tools(self) -> List[Tool]:
        """Get list of available MCP tools.
        
        Returns:
            List of MCP tool definitions
        """
        return [
            Tool(
                name="search_youtube_videos",
                description="Search for YouTube videos by query with advanced filtering options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for YouTube videos"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-50)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order for results",
                            "enum": ["relevance", "date", "rating", "viewCount", "title"],
                            "default": "relevance"
                        },
                        "published_after": {
                            "type": "string",
                            "description": "Only return videos published after this date (ISO 8601 format)",
                            "format": "date-time"
                        },
                        "published_before": {
                            "type": "string",
                            "description": "Only return videos published before this date (ISO 8601 format)",
                            "format": "date-time"
                        },
                        "duration": {
                            "type": "string",
                            "description": "Video duration filter",
                            "enum": ["any", "short", "medium", "long"],
                            "default": "any"
                        },
                        "video_definition": {
                            "type": "string",
                            "description": "Video quality filter",
                            "enum": ["any", "standard", "high"],
                            "default": "any"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_video_details",
                description="Get detailed information about specific YouTube videos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube video IDs to get details for",
                            "maxItems": 50
                        },
                        "include_statistics": {
                            "type": "boolean",
                            "description": "Include view count, like count, etc.",
                            "default": True
                        },
                        "include_content_details": {
                            "type": "boolean",
                            "description": "Include duration, definition, captions info",
                            "default": True
                        },
                        "include_snippet": {
                            "type": "boolean",
                            "description": "Include title, description, thumbnails",
                            "default": True
                        }
                    },
                    "required": ["video_ids"]
                }
            ),
            Tool(
                name="get_channel_info",
                description="Get information about YouTube channels",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube channel IDs",
                            "maxItems": 50
                        },
                        "channel_usernames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube channel usernames",
                            "maxItems": 50
                        },
                        "include_statistics": {
                            "type": "boolean",
                            "description": "Include subscriber count, video count, etc.",
                            "default": True
                        },
                        "include_content_details": {
                            "type": "boolean",
                            "description": "Include uploads playlist ID and other content details",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="get_channel_videos",
                description="Get videos from a specific YouTube channel",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "YouTube channel ID"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (1-50)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 25
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order for videos",
                            "enum": ["date", "rating", "relevance", "title", "viewCount"],
                            "default": "date"
                        },
                        "published_after": {
                            "type": "string",
                            "description": "Only return videos published after this date (ISO 8601 format)",
                            "format": "date-time"
                        },
                        "published_before": {
                            "type": "string",
                            "description": "Only return videos published before this date (ISO 8601 format)",
                            "format": "date-time"
                        }
                    },
                    "required": ["channel_id"]
                }
            ),
            Tool(
                name="get_video_comments",
                description="Get comments for YouTube videos with sentiment analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of comments to return (1-100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20
                        },
                        "order": {
                            "type": "string",
                            "description": "Sort order for comments",
                            "enum": ["time", "relevance"],
                            "default": "relevance"
                        },
                        "include_replies": {
                            "type": "boolean",
                            "description": "Include comment replies",
                            "default": False
                        },
                        "text_format": {
                            "type": "string",
                            "description": "Format for comment text",
                            "enum": ["html", "plainText"],
                            "default": "plainText"
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="get_video_transcript",
                description="Get transcript/captions for YouTube videos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID"
                        },
                        "language": {
                            "type": "string",
                            "description": "Preferred language code (e.g., 'en', 'es', 'fr')",
                            "default": "en"
                        },
                        "auto_generated": {
                            "type": "boolean",
                            "description": "Include auto-generated captions if manual ones aren't available",
                            "default": True
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format for transcript",
                            "enum": ["text", "srt", "vtt", "json"],
                            "default": "text"
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="analyze_video_performance",
                description="Analyze video performance metrics and engagement",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube video IDs to analyze",
                            "maxItems": 50
                        },
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "engagement_rate",
                                    "view_velocity",
                                    "retention_analysis",
                                    "comment_sentiment",
                                    "performance_score"
                                ]
                            },
                            "description": "Metrics to calculate",
                            "default": ["engagement_rate", "performance_score"]
                        },
                        "comparison_period": {
                            "type": "string",
                            "description": "Time period for performance comparison",
                            "enum": ["1d", "7d", "30d", "90d"],
                            "default": "30d"
                        }
                    },
                    "required": ["video_ids"]
                }
            ),
            Tool(
                name="get_trending_videos",
                description="Get trending videos by region and category",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "region_code": {
                            "type": "string",
                            "description": "ISO 3166-1 alpha-2 country code",
                            "default": "US"
                        },
                        "category_id": {
                            "type": "string",
                            "description": "YouTube category ID (optional)",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of trending videos to return (1-50)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 25
                        }
                    }
                }
            ),
            Tool(
                name="download_video",
                description="Download YouTube videos with multiple quality options and fallback methods",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID to download"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Video quality preference",
                            "enum": ["best", "worst", "720p", "480p", "360p", "240p"],
                            "default": "best"
                        },
                        "format_preference": {
                            "type": "string",
                            "description": "Preferred video format",
                            "enum": ["mp4", "webm", "mkv"],
                            "default": "mp4"
                        },
                        "audio_only": {
                            "type": "boolean",
                            "description": "Download audio only (MP3 format)",
                            "default": False
                        },
                        "include_subtitles": {
                            "type": "boolean",
                            "description": "Include subtitle/caption files",
                            "default": False
                        },
                        "subtitle_languages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Subtitle language codes (e.g., ['en', 'es', 'fr'])",
                            "default": ["en"]
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="get_download_formats",
                description="Get available download formats for a video without downloading",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID to check formats for"
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="cleanup_downloads",
                description="Clean up old downloaded files to free storage space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "older_than_hours": {
                            "type": "integer",
                            "description": "Delete files older than this many hours",
                            "minimum": 1,
                            "maximum": 168,
                            "default": 24
                        }
                    }
                }
            ),
            Tool(
                name="create_engagement_chart",
                description="Create visualization charts for video engagement metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_data": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of video data objects with statistics"
                        },
                        "chart_type": {
                            "type": "string",
                            "description": "Type of engagement chart to create",
                            "enum": ["bar", "scatter", "multi"],
                            "default": "bar"
                        }
                    },
                    "required": ["video_data"]
                }
            ),
            Tool(
                name="create_word_cloud",
                description="Create word cloud visualization from text data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text_data": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of text strings to analyze"
                        },
                        "source_type": {
                            "type": "string",
                            "description": "Type of text source for labeling",
                            "default": "titles"
                        }
                    },
                    "required": ["text_data"]
                }
            ),
            Tool(
                name="create_performance_radar",
                description="Create radar chart comparing video performance metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_data": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of video data objects with statistics"
                        },
                        "max_videos": {
                            "type": "integer",
                            "description": "Maximum number of videos to compare",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    },
                    "required": ["video_data"]
                }
            ),
            Tool(
                name="create_views_timeline",
                description="Create timeline visualization of video performance over time",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_data": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of video data objects with publication dates"
                        }
                    },
                    "required": ["video_data"]
                }
            ),
            Tool(
                name="create_comparison_heatmap",
                description="Create heatmap comparing multiple metrics across videos",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_data": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of video data objects with statistics"
                        }
                    },
                    "required": ["video_data"]
                }
            ),
            Tool(
                name="create_analysis_session",
                description="Create a new analysis session to organize related YouTube analysis work",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title for the analysis session"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the analysis goals",
                            "default": ""
                        },
                        "auto_switch": {
                            "type": "boolean",
                            "description": "Whether to automatically switch to this session",
                            "default": True
                        }
                    },
                    "required": ["title"]
                }
            ),
            Tool(
                name="list_analysis_sessions",
                description="List all available analysis sessions with their details",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="switch_analysis_session",
                description="Switch to a different analysis session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the session to switch to"
                        }
                    },
                    "required": ["session_id"]
                }
            ),
            Tool(
                name="get_session_video_ids",
                description="Get all video IDs from the current or specified analysis session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID (optional, uses current session if not provided)"
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format for video IDs",
                            "enum": ["list", "comma_separated", "detailed"],
                            "default": "list"
                        }
                    }
                }
            ),
            Tool(
                name="analyze_session_videos",
                description="Analyze all videos in the current session using stored video IDs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID (optional, uses current session if not provided)"
                        },
                        "include_visualizations": {
                            "type": "boolean",
                            "description": "Whether to create visualizations",
                            "default": True
                        },
                        "visualization_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["engagement_chart", "word_cloud", "performance_radar", "timeline", "heatmap"]
                            },
                            "description": "Types of visualizations to create",
                            "default": ["engagement_chart", "word_cloud", "performance_radar"]
                        }
                    }
                }
            ),
            Tool(
                name="extract_video_frames",
                description="Extract frames from a video file using ffmpeg for detailed visual analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID to download and extract frames from"
                        },
                        "video_path": {
                            "type": "string",
                            "description": "Path to local video file (alternative to video_id)"
                        },
                        "segment_start": {
                            "type": ["number", "string"],
                            "description": "Start time for extraction (seconds from beginning, 'end-X' for X seconds from end, or 'MM:SS' format)"
                        },
                        "segment_end": {
                            "type": ["number", "string"], 
                            "description": "End time for extraction (seconds from beginning, 'end-X' for X seconds from end, or 'MM:SS' format)"
                        },
                        "interval_seconds": {
                            "type": "number",
                            "description": "Time between extracted frames in seconds",
                            "minimum": 0.1,
                            "maximum": 60.0,
                            "default": 1.0
                        },
                        "max_frames": {
                            "type": "integer",
                            "description": "Maximum number of frames to extract",
                            "minimum": 1,
                            "maximum": 1000,
                            "default": 100
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Image format for extracted frames",
                            "enum": ["jpg", "png", "bmp"],
                            "default": "jpg"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Quality of extracted frames",
                            "enum": ["high", "medium", "low"],
                            "default": "high"
                        },
                        "resolution": {
                            "type": "string",
                            "description": "Output resolution (e.g., '1920x1080', '1280x720')",
                            "pattern": "^\\d+x\\d+$"
                        }
                    }
                }
            ),
            Tool(
                name="cleanup_extracted_frames",
                description="Clean up old extracted frame directories to free storage space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "older_than_hours": {
                            "type": "integer",
                            "description": "Delete frame directories older than this many hours",
                            "minimum": 1,
                            "maximum": 168,
                            "default": 24
                        }
                    }
                }
            ),
            Tool(
                name="analyze_video_content_from_frames",
                description="Extract frames from video(s) and provide comprehensive visual analysis including scenes, objects, people, and content summary",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube video IDs to analyze",
                            "maxItems": 10
                        },
                        "video_paths": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "List of local video file paths to analyze (alternative to video_ids)",
                            "maxItems": 10
                        },
                        "segment_start": {
                            "type": ["number", "string"],
                            "description": "Start time for analysis (seconds from beginning, 'end-X' for X seconds from end, or 'MM:SS' format)"
                        },
                        "segment_end": {
                            "type": ["number", "string"],
                            "description": "End time for analysis (seconds from beginning, 'end-X' for X seconds from end, or 'MM:SS' format)"
                        },
                        "frame_interval": {
                            "type": "number",
                            "description": "Time between analyzed frames in seconds",
                            "minimum": 0.5,
                            "maximum": 30.0,
                            "default": 2.0
                        },
                        "max_frames_per_video": {
                            "type": "integer",
                            "description": "Maximum number of frames to analyze per video",
                            "minimum": 5,
                            "maximum": 100,
                            "default": 20
                        },
                        "analysis_focus": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["scene_description", "objects", "people", "environment", "lighting", "composition", "text_content", "movement_indicators"]
                            },
                            "description": "Specific aspects to focus analysis on",
                            "default": ["scene_description", "objects", "people", "environment"]
                        },
                        "include_comparative_analysis": {
                            "type": "boolean",
                            "description": "Include comparative analysis across frames to identify patterns and progressions",
                            "default": True
                        },
                        "generate_video_summary": {
                            "type": "boolean", 
                            "description": "Generate comprehensive video content summary from frame analyses",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="generate_dashboard_artifact_prompt",
                description="Generate interactive HTML dashboard artifact prompt from current session analysis results",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to generate dashboard for (optional, uses current session if not provided)"
                        },
                        "include_video_analysis": {
                            "type": "boolean",
                            "description": "Include video frame analysis data in dashboard",
                            "default": True
                        },
                        "include_engagement_metrics": {
                            "type": "boolean",
                            "description": "Include engagement analysis in dashboard",
                            "default": True
                        },
                        "dashboard_title": {
                            "type": "string",
                            "description": "Custom title for the dashboard",
                            "default": "YouTube Analytics Dashboard"
                        },
                        "auto_generate": {
                            "type": "boolean",
                            "description": "Automatically provide instructions to create the artifact",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="analyze_video_frames_with_ai",
                description="Analyze extracted video frames using comprehensive AI prompts for detailed content analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID to analyze frames for"
                        },
                        "frame_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to extracted frame images (optional - will auto-detect if not provided)"
                        },
                        "analysis_focus": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific aspects to focus on in analysis",
                            "default": ["scene_description", "objects", "people", "environment", "lighting", "composition", "text_content"]
                        },
                        "generate_video_summary": {
                            "type": "boolean",
                            "description": "Generate comprehensive video summary from frame analyses",
                            "default": True
                        },
                        "max_frames_to_analyze": {
                            "type": "integer",
                            "description": "Maximum number of frames to analyze",
                            "default": 10
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="smart_trim_video",
                description="Intelligently trim videos using natural language instructions with AI-powered scene detection and audio analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string",
                            "description": "YouTube video URL to trim"
                        },
                        "trim_instructions": {
                            "type": "string",
                            "description": "Natural language instructions for trimming (e.g., 'first 30 seconds', 'scene with bird sounds', 'when person is speaking')"
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output video format",
                            "enum": ["mp4", "webm", "avi"],
                            "default": "mp4"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Output quality setting",
                            "enum": ["low", "medium", "high", "lossless"],
                            "default": "high"
                        },
                        "include_audio": {
                            "type": "boolean",
                            "description": "Whether to include audio in trimmed video",
                            "default": True
                        }
                    },
                    "required": ["video_url", "trim_instructions"]
                }
            ),
            Tool(
                name="detect_video_scenes",
                description="Detect scene changes in videos using computer vision techniques",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string", 
                            "description": "YouTube video URL to analyze"
                        },
                        "detection_method": {
                            "type": "string",
                            "description": "Scene detection method to use",
                            "enum": ["histogram", "optical_flow", "deep", "combined"],
                            "default": "combined"
                        },
                        "scene_threshold": {
                            "type": "number",
                            "description": "Sensitivity threshold for scene detection (0.1-1.0)",
                            "minimum": 0.1,
                            "maximum": 1.0,
                            "default": 0.3
                        }
                    },
                    "required": ["video_url"]
                }
            ),
            Tool(
                name="analyze_audio_patterns",
                description="Analyze audio patterns and events in videos using AI-powered sound classification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string",
                            "description": "YouTube video URL to analyze"
                        },
                        "target_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific audio patterns to detect (e.g., 'bird sounds', 'music', 'applause')"
                        },
                        "include_transcription": {
                            "type": "boolean",
                            "description": "Include speech transcription using Whisper",
                            "default": True
                        }
                    },
                    "required": ["video_url"]
                }
            ),
            Tool(
                name="extract_content_segments",
                description="Extract video segments based on specific content criteria using AI analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string",
                            "description": "YouTube video URL to process"
                        },
                        "segment_criteria": {
                            "type": "object",
                            "description": "Criteria for segment extraction",
                            "properties": {
                                "audio_pattern": {
                                    "type": "string",
                                    "description": "Audio pattern to search for"
                                },
                                "objects": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Objects to detect in video"
                                },
                                "confidence_threshold": {
                                    "type": "number",
                                    "description": "Minimum confidence for detections",
                                    "default": 0.5
                                },
                                "extract_audio": {
                                    "type": "boolean",
                                    "description": "Also extract audio segments",
                                    "default": False
                                }
                            }
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save extracted segments"
                        },
                        "context_window": {
                            "type": "number",
                            "description": "Seconds to include before/after detected content",
                            "default": 2.0
                        }
                    },
                    "required": ["video_url", "segment_criteria", "output_dir"]
                }
            )
        ]
        
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Execute a specific tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution results
            
        Raises:
            ValidationError: If tool name or arguments are invalid
            YouTubeAPIError: If YouTube API call fails
        """
        try:
            if name == "search_youtube_videos":
                return await self._search_youtube_videos(**arguments)
            elif name == "get_video_details":
                return await self._get_video_details(**arguments)
            elif name == "get_channel_info":
                return await self._get_channel_info(**arguments)
            elif name == "get_channel_videos":
                return await self._get_channel_videos(**arguments)
            elif name == "get_video_comments":
                return await self._get_video_comments(**arguments)
            elif name == "get_video_transcript":
                return await self._get_video_transcript(**arguments)
            elif name == "analyze_video_performance":
                return await self._analyze_video_performance(**arguments)
            elif name == "get_trending_videos":
                return await self._get_trending_videos(**arguments)
            elif name == "download_video":
                return await self._download_video(**arguments)
            elif name == "get_download_formats":
                return await self._get_download_formats(**arguments)
            elif name == "cleanup_downloads":
                return await self._cleanup_downloads(**arguments)
            elif name == "create_engagement_chart":
                return await self._create_engagement_chart(**arguments)
            elif name == "create_word_cloud":
                return await self._create_word_cloud(**arguments)
            elif name == "create_performance_radar":
                return await self._create_performance_radar(**arguments)
            elif name == "create_views_timeline":
                return await self._create_views_timeline(**arguments)
            elif name == "create_comparison_heatmap":
                return await self._create_comparison_heatmap(**arguments)
            elif name == "create_analysis_session":
                return await self._create_analysis_session(**arguments)
            elif name == "list_analysis_sessions":
                return await self._list_analysis_sessions(**arguments)
            elif name == "switch_analysis_session":
                return await self._switch_analysis_session(**arguments)
            elif name == "get_session_video_ids":
                return await self._get_session_video_ids(**arguments)
            elif name == "analyze_session_videos":
                return await self._analyze_session_videos(**arguments)
            elif name == "extract_video_frames":
                return await self._extract_video_frames(**arguments)
            elif name == "cleanup_extracted_frames":
                return await self._cleanup_extracted_frames(**arguments)
            elif name == "analyze_video_content_from_frames":
                return await self._analyze_video_content_from_frames(**arguments)
            elif name == "generate_dashboard_artifact_prompt":
                return await self._generate_dashboard_artifact_prompt(**arguments)
            elif name == "analyze_video_frames_with_ai":
                return await self._analyze_video_frames_with_ai(**arguments)
            elif name == "smart_trim_video":
                return await self._smart_trim_video(**arguments)
            elif name == "detect_video_scenes":
                return await self._detect_video_scenes(**arguments)
            elif name == "analyze_audio_patterns":
                return await self._analyze_audio_patterns(**arguments)
            elif name == "extract_content_segments":
                return await self._extract_content_segments(**arguments)
            else:
                raise ValidationError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Tool execution failed for {name}: {e}")
            await self.error_handler.handle_error(e, {"tool": name, "arguments": arguments})
            raise
            
    async def _search_youtube_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        duration: str = "any",
        video_definition: str = "any"
    ) -> List[TextContent]:
        """Search for YouTube videos."""
        logger.info(f"Searching YouTube videos: query='{query}', max_results={max_results}")
        
        search_params = {
            "query": query,
            "max_results": max_results,
            "order": order
        }
        
        if published_after:
            search_params["published_after"] = published_after
        if published_before:
            search_params["published_before"] = published_before
            
        results = await self.api_client.search_videos(**search_params)
        
        # Convert results to dictionaries if they're model objects
        videos_data = []
        for result in results:
            if hasattr(result, 'model_dump'):
                videos_data.append(result.model_dump())
            elif hasattr(result, '__dict__'):
                videos_data.append(result.__dict__)
            else:
                videos_data.append(result)
        
        # Format results for MCP response
        response_data = {
            "query": query,
            "total_results": len(videos_data),
            "search_parameters": search_params,
            "videos": videos_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Automatically save search results to resource manager
        try:
            resource_uri = self.resource_manager.save_search_results(
                query=query,
                results=videos_data
            )
            response_data["resource_uri"] = resource_uri
            response_data["saved_to_session"] = True
            
            # Add session context
            current_session = self.resource_manager.get_session()
            if current_session:
                response_data["session_info"] = {
                    "session_id": current_session.session_id,
                    "session_title": current_session.title,
                    "total_video_ids": len(current_session.video_ids)
                }
            
            logger.info(f"Search results automatically saved to resource: {resource_uri}")
            
        except Exception as e:
            logger.warning(f"Failed to save search results to resource manager: {e}")
            response_data["resource_save_error"] = str(e)
            response_data["saved_to_session"] = False
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_video_details(
        self,
        video_ids: List[str],
        include_statistics: bool = True,
        include_content_details: bool = True,
        include_snippet: bool = True
    ) -> List[TextContent]:
        """Get detailed video information."""
        logger.info(f"Getting video details for {len(video_ids)} videos")
        
        parts = []
        if include_snippet:
            parts.append("snippet")
        if include_statistics:
            parts.append("statistics")
        if include_content_details:
            parts.append("contentDetails")
            
        results = await self.api_client.get_video_details(video_ids, parts)
        
        response_data = {
            "video_count": len(results),
            "requested_parts": parts,
            "videos": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Automatically save video details to resource manager
        try:
            resource_uri = self.resource_manager.save_video_details(
                video_details=results
            )
            response_data["resource_uri"] = resource_uri
            response_data["saved_to_session"] = True
            
            # Add session context
            current_session = self.resource_manager.get_session()
            if current_session:
                response_data["session_info"] = {
                    "session_id": current_session.session_id,
                    "session_title": current_session.title,
                    "total_video_ids": len(current_session.video_ids)
                }
            
            logger.info(f"Video details automatically saved to resource: {resource_uri}")
            
        except Exception as e:
            logger.warning(f"Failed to save video details to resource manager: {e}")
            response_data["resource_save_error"] = str(e)
            response_data["saved_to_session"] = False
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_channel_info(
        self,
        channel_ids: Optional[List[str]] = None,
        channel_usernames: Optional[List[str]] = None,
        include_statistics: bool = True,
        include_content_details: bool = True
    ) -> List[TextContent]:
        """Get channel information."""
        if not channel_ids and not channel_usernames:
            raise ValidationError("Either channel_ids or channel_usernames must be provided")
            
        logger.info(f"Getting channel info for {len(channel_ids or []) + len(channel_usernames or [])} channels")
        
        parts = ["snippet"]
        if include_statistics:
            parts.append("statistics")
        if include_content_details:
            parts.append("contentDetails")
            
        results = await self.api_client.get_channel_info(
            channel_ids=channel_ids,
            channel_usernames=channel_usernames,
            parts=parts
        )
        
        response_data = {
            "channel_count": len(results),
            "requested_parts": parts,
            "channels": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 25,
        order: str = "date",
        published_after: Optional[str] = None,
        published_before: Optional[str] = None
    ) -> List[TextContent]:
        """Get videos from a channel."""
        logger.info(f"Getting videos from channel {channel_id}")
        
        search_params = {
            "channel_id": channel_id,
            "max_results": max_results,
            "order": order
        }
        
        if published_after:
            search_params["published_after"] = published_after
        if published_before:
            search_params["published_before"] = published_before
            
        results = await self.api_client.get_channel_videos(
            channel_id=channel_id,
            max_results=max_results,
            order=order
        )
        
        # Convert SearchResult objects to dictionaries
        videos_data = []
        for result in results:
            if hasattr(result, 'model_dump'):
                videos_data.append(result.model_dump())
            elif hasattr(result, '__dict__'):
                videos_data.append(result.__dict__)
            else:
                videos_data.append(result)
        
        response_data = {
            "channel_id": channel_id,
            "video_count": len(videos_data),
            "search_parameters": search_params,
            "videos": videos_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_video_comments(
        self,
        video_id: str,
        max_results: int = 20,
        order: str = "relevance",
        include_replies: bool = False,
        text_format: str = "plainText"
    ) -> List[TextContent]:
        """Get video comments."""
        logger.info(f"Getting comments for video {video_id}")
        
        results = await self.api_client.get_video_comments(
            video_id=video_id,
            max_results=max_results,
            order=order,
            include_replies=include_replies,
            text_format=text_format
        )
        
        response_data = {
            "video_id": video_id,
            "comment_count": len(results),
            "parameters": {
                "max_results": max_results,
                "order": order,
                "include_replies": include_replies,
                "text_format": text_format
            },
            "comments": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_video_transcript(
        self,
        video_id: str,
        language: str = "en",
        auto_generated: bool = True,
        format: str = "text"
    ) -> List[TextContent]:
        """Get video transcript."""
        logger.info(f"Getting transcript for video {video_id}")
        
        try:
            transcript_data = await self.api_client.get_video_transcript(
                video_id=video_id,
                language=language,
                auto_generated=auto_generated
            )
            
            if format == "text":
                text_content = transcript_data.get("text", "")
            elif format == "json":
                text_content = json.dumps(transcript_data, indent=2, ensure_ascii=False)
            else:
                # For SRT and VTT formats, format the transcript accordingly
                text_content = self._format_transcript(transcript_data, format)
                
            response_data = {
                "video_id": video_id,
                "language": language,
                "format": format,
                "auto_generated": transcript_data.get("auto_generated", False),
                "transcript": text_content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.warning(f"Could not get transcript for video {video_id}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "video_id": video_id,
                    "error": str(e),
                    "transcript": None,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _analyze_video_performance(
        self,
        video_ids: List[str],
        metrics: List[str] = None,
        comparison_period: str = "30d"
    ) -> List[TextContent]:
        """Analyze video performance metrics."""
        if metrics is None:
            metrics = ["engagement_rate", "performance_score"]
            
        logger.info(f"Analyzing performance for {len(video_ids)} videos")
        
        # Get video details first
        video_details = await self.api_client.get_video_details(
            video_ids, 
            ["snippet", "statistics", "contentDetails"]
        )
        
        # Calculate requested metrics
        analysis_results = []
        for video in video_details:
            video_analysis = {
                "video_id": video["id"],
                "title": video.get("snippet", {}).get("title", ""),
                "metrics": {}
            }
            
            statistics = video.get("statistics", {})
            
            if "engagement_rate" in metrics:
                view_count = int(statistics.get("viewCount", 0))
                like_count = int(statistics.get("likeCount", 0))
                comment_count = int(statistics.get("commentCount", 0))
                
                if view_count > 0:
                    engagement_rate = ((like_count + comment_count) / view_count) * 100
                    video_analysis["metrics"]["engagement_rate"] = round(engagement_rate, 4)
                    
            if "performance_score" in metrics:
                # Simple performance score based on views, likes, and recency
                view_count = int(statistics.get("viewCount", 0))
                like_count = int(statistics.get("likeCount", 0))
                
                published_at = video.get("snippet", {}).get("publishedAt", "")
                if published_at:
                    try:
                        # Parse published date with proper timezone handling
                        if published_at.endswith('Z'):
                            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        else:
                            published_date = datetime.fromisoformat(published_at)
                        
                        # Ensure both datetimes are timezone-aware
                        now_utc = datetime.now(published_date.tzinfo) if published_date.tzinfo else datetime.utcnow()
                        
                        days_since_publish = (now_utc - published_date).days
                        recency_factor = max(0.1, 1 / (1 + days_since_publish / 30))  # Decay over time
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse published date {published_at}: {e}")
                        recency_factor = 0.5
                else:
                    recency_factor = 0.5
                    
                performance_score = (view_count * 0.6 + like_count * 0.4) * recency_factor
                video_analysis["metrics"]["performance_score"] = round(performance_score, 2)
                
            analysis_results.append(video_analysis)
            
        response_data = {
            "video_count": len(video_ids),
            "requested_metrics": metrics,
            "comparison_period": comparison_period,
            "analysis": analysis_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    async def _get_trending_videos(
        self,
        region_code: str = "US",
        category_id: Optional[str] = None,
        max_results: int = 25
    ) -> List[TextContent]:
        """Get trending videos."""
        logger.info(f"Getting trending videos for region {region_code}")
        
        results = await self.api_client.get_trending_videos(
            region_code=region_code,
            category_id=category_id,
            max_results=max_results
        )
        
        # Convert SearchResult objects to dictionaries
        videos_data = []
        for result in results:
            if hasattr(result, 'model_dump'):
                videos_data.append(result.model_dump())
            elif hasattr(result, '__dict__'):
                videos_data.append(result.__dict__)
            else:
                videos_data.append(result)
        
        response_data = {
            "region_code": region_code,
            "category_id": category_id,
            "video_count": len(videos_data),
            "videos": videos_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response_data, indent=2, ensure_ascii=False)
        )]
        
    def _format_transcript(self, transcript_data: Dict[str, Any], format: str) -> str:
        """Format transcript in specified format.
        
        Args:
            transcript_data: Raw transcript data
            format: Desired format (srt, vtt)
            
        Returns:
            Formatted transcript text
        """
        segments = transcript_data.get("segments", [])
        
        if format == "srt":
            formatted_lines = []
            for i, segment in enumerate(segments, 1):
                start_time = self._seconds_to_srt_time(segment.get("start", 0))
                end_time = self._seconds_to_srt_time(segment.get("start", 0) + segment.get("duration", 0))
                text = segment.get("text", "").strip()
                
                formatted_lines.extend([
                    str(i),
                    f"{start_time} --> {end_time}",
                    text,
                    ""
                ])
            return "\n".join(formatted_lines)
            
        elif format == "vtt":
            formatted_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = self._seconds_to_vtt_time(segment.get("start", 0))
                end_time = self._seconds_to_vtt_time(segment.get("start", 0) + segment.get("duration", 0))
                text = segment.get("text", "").strip()
                
                formatted_lines.extend([
                    f"{start_time} --> {end_time}",
                    text,
                    ""
                ])
            return "\n".join(formatted_lines)
            
        return transcript_data.get("text", "")
        
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
        
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        
    async def _download_video(
        self,
        video_id: str,
        quality: str = "best",
        format_preference: str = "mp4",
        audio_only: bool = False,
        include_subtitles: bool = False,
        subtitle_languages: List[str] = None
    ) -> List[TextContent]:
        """Download video with specified options."""
        logger.info(f"Downloading video {video_id} with quality={quality}, format={format_preference}")
        
        if subtitle_languages is None:
            subtitle_languages = ["en"]
            
        try:
            result = await self.video_downloader.download_video(
                video_id=video_id,
                quality=quality,
                format_preference=format_preference,
                audio_only=audio_only,
                include_subtitles=include_subtitles,
                subtitle_languages=subtitle_languages
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Video download failed for {video_id}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "video_id": video_id,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _get_download_formats(self, video_id: str) -> List[TextContent]:
        """Get available download formats for a video."""
        logger.info(f"Getting download formats for video {video_id}")
        
        try:
            result = await self.video_downloader.get_download_formats(video_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to get formats for video {video_id}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "video_id": video_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _cleanup_downloads(self, older_than_hours: int = 24) -> List[TextContent]:
        """Clean up old download files."""
        logger.info(f"Cleaning up downloads older than {older_than_hours} hours")
        
        try:
            result = await self.video_downloader.cleanup_downloads(older_than_hours)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_engagement_chart(
        self,
        video_data: List[Dict[str, Any]],
        chart_type: str = "bar"
    ) -> List[TextContent]:
        """Create engagement chart visualization."""
        logger.info(f"Creating engagement chart with {len(video_data)} videos")
        
        try:
            result = self.visualization_tools.create_engagement_chart(video_data, chart_type)
            
            response_data = {
                "visualization_type": "engagement_chart",
                "chart_type": chart_type,
                "video_count": len(video_data),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Automatically save visualization to resource manager
            try:
                resource_uri = self.resource_manager.save_visualization(
                    viz_type="engagement_chart",
                    viz_data=result
                )
                response_data["resource_uri"] = resource_uri
                response_data["saved_to_session"] = True
                
                current_session = self.resource_manager.get_session()
                if current_session:
                    response_data["session_info"] = {
                        "session_id": current_session.session_id,
                        "session_title": current_session.title
                    }
                
                logger.info(f"Engagement chart automatically saved to resource: {resource_uri}")
                
            except Exception as save_error:
                logger.warning(f"Failed to save visualization to resource manager: {save_error}")
                response_data["resource_save_error"] = str(save_error)
                response_data["saved_to_session"] = False
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create engagement chart: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "engagement_chart",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_word_cloud(
        self,
        text_data: List[str],
        source_type: str = "titles"
    ) -> List[TextContent]:
        """Create word cloud visualization."""
        logger.info(f"Creating word cloud from {len(text_data)} text items")
        
        try:
            result = self.visualization_tools.create_word_cloud(text_data, source_type)
            
            response_data = {
                "visualization_type": "word_cloud",
                "source_type": source_type,
                "text_count": len(text_data),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Automatically save visualization to resource manager
            try:
                resource_uri = self.resource_manager.save_visualization(
                    viz_type="word_cloud",
                    viz_data=result
                )
                response_data["resource_uri"] = resource_uri
                response_data["saved_to_session"] = True
                
                current_session = self.resource_manager.get_session()
                if current_session:
                    response_data["session_info"] = {
                        "session_id": current_session.session_id,
                        "session_title": current_session.title
                    }
                
                logger.info(f"Word cloud automatically saved to resource: {resource_uri}")
                
            except Exception as save_error:
                logger.warning(f"Failed to save visualization to resource manager: {save_error}")
                response_data["resource_save_error"] = str(save_error)
                response_data["saved_to_session"] = False
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create word cloud: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "word_cloud",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_performance_radar(
        self,
        video_data: List[Dict[str, Any]],
        max_videos: int = 5
    ) -> List[TextContent]:
        """Create performance radar chart."""
        logger.info(f"Creating performance radar chart with {len(video_data)} videos")
        
        try:
            result = self.visualization_tools.create_performance_radar(video_data, max_videos)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "performance_radar",
                    "video_count": len(video_data),
                    "max_videos": max_videos,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create performance radar: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "performance_radar",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_views_timeline(
        self,
        video_data: List[Dict[str, Any]]
    ) -> List[TextContent]:
        """Create views timeline visualization."""
        logger.info(f"Creating views timeline with {len(video_data)} videos")
        
        try:
            result = self.visualization_tools.create_views_timeline(video_data)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "views_timeline",
                    "video_count": len(video_data),
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create views timeline: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "views_timeline",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_comparison_heatmap(
        self,
        video_data: List[Dict[str, Any]]
    ) -> List[TextContent]:
        """Create comparison heatmap visualization."""
        logger.info(f"Creating comparison heatmap with {len(video_data)} videos")
        
        try:
            result = self.visualization_tools.create_comparison_heatmap(video_data)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "comparison_heatmap",
                    "video_count": len(video_data),
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create comparison heatmap: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "visualization_type": "comparison_heatmap",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _create_analysis_session(
        self,
        title: str,
        description: str = "",
        auto_switch: bool = True
    ) -> List[TextContent]:
        """Create a new analysis session."""
        logger.info(f"Creating new analysis session: {title}")
        
        try:
            session_id = self.resource_manager.create_session(
                title=title,
                description=description,
                auto_switch=auto_switch
            )
            
            session = self.resource_manager.get_session(session_id)
            
            response_data = {
                "success": True,
                "session_id": session_id,
                "title": title,
                "description": description,
                "created_at": session.created_at.isoformat() if session else datetime.utcnow().isoformat(),
                "auto_switched": auto_switch,
                "message": f"Analysis session '{title}' created successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to create analysis session: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to create analysis session",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _list_analysis_sessions(self) -> List[TextContent]:
        """List all available analysis sessions."""
        logger.info("Listing all analysis sessions")
        
        try:
            sessions_data = []
            current_session_id = self.resource_manager.current_session_id
            
            for session in self.resource_manager.sessions.values():
                session_info = {
                    "session_id": session.session_id,
                    "title": session.title,
                    "description": session.description,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "video_count": len(session.video_ids),
                    "search_queries": session.search_queries,
                    "resource_count": len(session.resources),
                    "is_current": session.session_id == current_session_id
                }
                sessions_data.append(session_info)
            
            # Sort by updated_at descending (most recent first)
            sessions_data.sort(key=lambda x: x["updated_at"], reverse=True)
            
            response_data = {
                "success": True,
                "total_sessions": len(sessions_data),
                "current_session_id": current_session_id,
                "sessions": sessions_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to list analysis sessions: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to list analysis sessions",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _switch_analysis_session(
        self,
        session_id: str
    ) -> List[TextContent]:
        """Switch to a different analysis session."""
        logger.info(f"Switching to analysis session: {session_id}")
        
        try:
            success = self.resource_manager.switch_session(session_id)
            
            if success:
                session = self.resource_manager.get_session(session_id)
                response_data = {
                    "success": True,
                    "session_id": session_id,
                    "title": session.title if session else "Unknown",
                    "description": session.description if session else "",
                    "video_count": len(session.video_ids) if session else 0,
                    "resource_count": len(session.resources) if session else 0,
                    "message": f"Successfully switched to session '{session.title if session else session_id}'",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                response_data = {
                    "success": False,
                    "error": "Session not found",
                    "session_id": session_id,
                    "message": f"Session '{session_id}' does not exist",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to switch analysis session: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to switch analysis session",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _get_session_video_ids(
        self,
        session_id: Optional[str] = None,
        format: str = "list"
    ) -> List[TextContent]:
        """Get all video IDs from the current or specified analysis session."""
        logger.info(f"Getting video IDs from session: {session_id or 'current'}")
        
        try:
            session = self.resource_manager.get_session(session_id)
            
            if not session:
                if session_id:
                    error_msg = f"Session '{session_id}' not found"
                else:
                    error_msg = "No current session is active"
                    
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            video_ids = list(session.video_ids)
            
            # Format output based on requested format
            if format == "comma_separated":
                formatted_ids = ", ".join(video_ids)
            elif format == "detailed":
                formatted_ids = [
                    {
                        "video_id": vid_id,
                        "url": f"https://www.youtube.com/watch?v={vid_id}"
                    } for vid_id in video_ids
                ]
            else:  # Default to list format
                formatted_ids = video_ids
            
            response_data = {
                "success": True,
                "session_id": session.session_id,
                "session_title": session.title,
                "video_count": len(video_ids),
                "format": format,
                "video_ids": formatted_ids,
                "message": f"Retrieved {len(video_ids)} video IDs from session '{session.title}'",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to get session video IDs: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get session video IDs",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _analyze_session_videos(
        self,
        session_id: Optional[str] = None,
        include_visualizations: bool = True,
        visualization_types: List[str] = None
    ) -> List[TextContent]:
        """Analyze all videos in the current session using stored video IDs."""
        logger.info(f"Analyzing videos in session: {session_id or 'current'}")
        
        if visualization_types is None:
            visualization_types = ["engagement_chart", "word_cloud", "performance_radar"]
        
        try:
            session = self.resource_manager.get_session(session_id)
            
            if not session:
                if session_id:
                    error_msg = f"Session '{session_id}' not found"
                else:
                    error_msg = "No current session is active"
                    
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            video_ids = list(session.video_ids)
            
            if not video_ids:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "No video IDs found in session",
                        "session_id": session.session_id,
                        "session_title": session.title,
                        "message": f"Session '{session.title}' contains no video IDs to analyze",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Get detailed video information with batch processing
            # YouTube API allows max 50 videos per request
            BATCH_SIZE = 50
            all_video_data = []
            
            logger.info(f"Processing {len(video_ids)} videos in batches of {BATCH_SIZE}")
            
            for i in range(0, len(video_ids), BATCH_SIZE):
                batch_ids = video_ids[i:i + BATCH_SIZE]
                logger.info(f"Processing batch {i//BATCH_SIZE + 1}: videos {i+1}-{min(i+BATCH_SIZE, len(video_ids))}")
                
                try:
                    batch_result = await self._get_video_details(
                        video_ids=batch_ids,
                        include_statistics=True,
                        include_content_details=True,
                        include_snippet=True
                    )
                    
                    # Parse batch results
                    batch_json = json.loads(batch_result[0].text)
                    batch_videos = batch_json.get("videos", [])
                    all_video_data.extend(batch_videos)
                    
                except Exception as e:
                    logger.warning(f"Failed to process batch {i//BATCH_SIZE + 1}: {e}")
                    # Continue with other batches
                    continue
            
            # Use the aggregated video data from all batches
            video_data = all_video_data
            logger.info(f"Successfully processed {len(video_data)} videos from {len(video_ids)} requested")
            
            # Perform analysis on successfully retrieved videos only
            successful_video_ids = [video.get("id") for video in video_data if video.get("id")]
            
            if successful_video_ids:
                analysis_result = await self._analyze_video_performance(
                    video_ids=successful_video_ids,
                    metrics=["engagement_rate", "performance_score"],
                    comparison_period="30d"
                )
                analysis_json = json.loads(analysis_result[0].text)
            else:
                logger.warning("No successful video data retrieved for analysis")
                analysis_json = {"analysis": []}
            
            # Store analysis results
            analysis_uri = self.resource_manager.save_video_details(
                video_data, session.session_id
            )
            
            # Create visualizations if requested
            visualization_results = []
            if include_visualizations and video_data:
                
                for viz_type in visualization_types:
                    try:
                        if viz_type == "engagement_chart":
                            viz_result = await self._create_engagement_chart(
                                video_data=video_data,
                                chart_type="multi"
                            )
                        elif viz_type == "word_cloud":
                            titles = [video.get("snippet", {}).get("title", "") for video in video_data]
                            viz_result = await self._create_word_cloud(
                                text_data=titles,
                                source_type="titles"
                            )
                        elif viz_type == "performance_radar":
                            viz_result = await self._create_performance_radar(
                                video_data=video_data,
                                max_videos=min(5, len(video_data))
                            )
                        elif viz_type == "timeline":
                            viz_result = await self._create_views_timeline(
                                video_data=video_data
                            )
                        elif viz_type == "heatmap":
                            viz_result = await self._create_comparison_heatmap(
                                video_data=video_data
                            )
                        else:
                            continue
                        
                        viz_data = json.loads(viz_result[0].text)
                        if viz_data.get("result", {}).get("success", False):
                            # Save visualization to resource manager
                            viz_uri = self.resource_manager.save_visualization(
                                viz_type=viz_type,
                                viz_data=viz_data["result"],
                                session_id=session.session_id
                            )
                            visualization_results.append({
                                "type": viz_type,
                                "success": True,
                                "resource_uri": viz_uri,
                                "data": viz_data
                            })
                        else:
                            visualization_results.append({
                                "type": viz_type,
                                "success": False,
                                "error": viz_data.get("error", "Unknown error")
                            })
                            
                    except Exception as viz_error:
                        logger.warning(f"Failed to create {viz_type} visualization: {viz_error}")
                        visualization_results.append({
                            "type": viz_type,
                            "success": False,
                            "error": str(viz_error)
                        })
            
            # Compile final response
            response_data = {
                "success": True,
                "session_id": session.session_id,
                "session_title": session.title,
                "analysis": {
                    "video_count": len(video_ids),
                    "analyzed_videos": len(video_data),
                    "performance_metrics": analysis_json.get("analysis", []),
                    "analysis_resource_uri": analysis_uri
                },
                "visualizations": {
                    "created": include_visualizations,
                    "requested_types": visualization_types,
                    "results": visualization_results,
                    "successful_count": len([v for v in visualization_results if v.get("success", False)])
                },
                "summary": {
                    "total_resources": len(session.resources),
                    "video_ids_analyzed": video_ids,
                    "session_updated": session.updated_at.isoformat()
                },
                "message": f"Successfully analyzed {len(video_data)} videos from session '{session.title}'",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Auto-generate dashboard prompt if visualizations were created successfully
            successful_viz_count = len([v for v in visualization_results if v.get("success", False)])
            if successful_viz_count > 0:
                try:
                    # Generate dashboard prompt automatically
                    dashboard_prompt = dashboard_prompt_generator.generate_auto_dashboard_prompt(
                        session_data={
                            "session_id": session.session_id,
                            "session_title": session.title
                        },
                        analysis_results=response_data
                    )
                    
                    response_data["dashboard_generation"] = {
                        "available": True,
                        "prompt": dashboard_prompt,
                        "instruction": "🎨 Analysis complete! Create an interactive HTML dashboard artifact using the prompt above to visualize these results.",
                        "visualization_count": successful_viz_count
                    }
                    
                    logger.info(f"Auto-generated dashboard prompt for session {session.session_id}")
                    
                except Exception as dashboard_error:
                    logger.warning(f"Failed to auto-generate dashboard prompt: {dashboard_error}")
                    response_data["dashboard_generation"] = {
                        "available": False,
                        "error": str(dashboard_error)
                    }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to analyze session videos: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to analyze session videos",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
            
    async def _extract_video_frames(
        self,
        video_id: Optional[str] = None,
        video_path: Optional[str] = None,
        segment_start: Optional[Union[int, str]] = None,
        segment_end: Optional[Union[int, str]] = None,
        interval_seconds: float = 1.0,
        max_frames: int = 100,
        output_format: str = "jpg",
        quality: str = "high",
        resolution: Optional[str] = None
    ) -> List[TextContent]:
        """Extract frames from a video for analysis."""
        logger.info(f"Extracting frames from video: {video_id or video_path}")
        
        try:
            # Determine video source
            if video_id and not video_path:
                # Download video first
                logger.info(f"Downloading video {video_id} for frame extraction")
                download_result = await self._download_video(
                    video_id=video_id,
                    quality="best",
                    audio_only=False
                )
                
                # Parse download result to get file path
                download_data = json.loads(download_result[0].text)
                if not download_data.get("success", False):
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": f"Failed to download video {video_id}: {download_data.get('error', 'Unknown error')}",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    )]
                
                video_path = download_data.get("file_path")
                if not video_path or not Path(video_path).exists():
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": f"Downloaded video file not found: {video_path}",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    )]
            
            elif not video_path:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Either video_id or video_path must be provided",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Verify video file exists
            if not Path(video_path).exists():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Video file not found: {video_path}",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Create extraction configuration
            config = FrameExtractionConfig(
                segment_start=segment_start,
                segment_end=segment_end,
                interval_seconds=interval_seconds,
                max_frames=max_frames,
                output_format=output_format,
                quality=quality,
                resolution=resolution
            )
            
            # Extract frames
            result = await self.frame_extractor.extract_frames(
                video_path=video_path,
                config=config,
                output_prefix=f"frames_{video_id or Path(video_path).stem}"
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _cleanup_extracted_frames(self, older_than_hours: int = 24) -> List[TextContent]:
        """Clean up old extracted frame directories."""
        logger.info(f"Cleaning up extracted frames older than {older_than_hours} hours")
        
        try:
            result = await self.frame_extractor.cleanup_frames(older_than_hours)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Frame cleanup failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _analyze_video_content_from_frames(
        self,
        video_ids: Optional[List[str]] = None,
        video_paths: Optional[List[str]] = None,
        segment_start: Optional[Union[int, str]] = None,
        segment_end: Optional[Union[int, str]] = None,
        frame_interval: float = 2.0,
        max_frames_per_video: int = 20,
        analysis_focus: List[str] = None,
        include_comparative_analysis: bool = True,
        generate_video_summary: bool = True
    ) -> List[TextContent]:
        """Extract frames from videos and provide comprehensive visual analysis."""
        logger.info(f"Starting comprehensive video content analysis for {len(video_ids or video_paths or [])} videos")
        
        if analysis_focus is None:
            analysis_focus = ["scene_description", "objects", "people", "environment"]
        
        try:
            # Validate inputs
            if not video_ids and not video_paths:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Either video_ids or video_paths must be provided",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Process videos (either IDs or paths)
            videos_to_process = []
            if video_ids:
                for video_id in video_ids:
                    videos_to_process.append({"type": "id", "value": video_id})
            if video_paths:
                for video_path in video_paths:
                    videos_to_process.append({"type": "path", "value": video_path})
            
            all_analysis_results = []
            processing_summary = []
            
            for i, video_info in enumerate(videos_to_process):
                logger.info(f"Processing video {i+1}/{len(videos_to_process)}: {video_info['value']}")
                
                try:
                    # Extract frames for this video
                    if video_info["type"] == "id":
                        frames_result = await self._extract_video_frames(
                            video_id=video_info["value"],
                            segment_start=segment_start,
                            segment_end=segment_end,
                            interval_seconds=frame_interval,
                            max_frames=max_frames_per_video,
                            quality="medium",  # Balance quality vs processing time
                            output_format="jpg"
                        )
                    else:  # video_path
                        frames_result = await self._extract_video_frames(
                            video_path=video_info["value"],
                            segment_start=segment_start,
                            segment_end=segment_end,
                            interval_seconds=frame_interval,
                            max_frames=max_frames_per_video,
                            quality="medium",
                            output_format="jpg"
                        )
                    
                    # Parse frame extraction results
                    frames_data = json.loads(frames_result[0].text)
                    
                    if not frames_data.get("success"):
                        logger.warning(f"Frame extraction failed for {video_info['value']}: {frames_data.get('error', 'Unknown error')}")
                        processing_summary.append({
                            "video": video_info["value"],
                            "status": "failed",
                            "error": f"Frame extraction failed: {frames_data.get('error', 'Unknown error')}"
                        })
                        continue
                    
                    extracted_frames = frames_data.get("frames", [])
                    if not extracted_frames:
                        logger.warning(f"No frames extracted for {video_info['value']}")
                        processing_summary.append({
                            "video": video_info["value"],
                            "status": "failed",
                            "error": "No frames were extracted"
                        })
                        continue
                    
                    logger.info(f"Successfully extracted {len(extracted_frames)} frames from {video_info['value']}")
                    
                    # Generate analysis prompts for each frame
                    frame_analyses = []
                    for frame_info in extracted_frames:
                        try:
                            # Generate comprehensive frame analysis prompt
                            analysis_prompt = VideoFrameAnalysisPrompts.get_comprehensive_frame_analysis_prompt(
                                frame_info=frame_info,
                                analysis_focus=analysis_focus
                            )
                            
                            # For this implementation, we'll store the prompt and frame info
                            # In a real deployment, this would be sent to an image analysis service
                            frame_analysis = {
                                "frame_info": frame_info,
                                "analysis_prompt": analysis_prompt,
                                "analysis_status": "prompt_generated",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            frame_analyses.append(frame_analysis)
                            
                        except Exception as frame_error:
                            logger.warning(f"Failed to generate analysis for frame {frame_info.get('frame_number', 'unknown')}: {frame_error}")
                            continue
                    
                    # Generate comparative analysis prompt if requested
                    comparative_analysis = None
                    if include_comparative_analysis and len(frame_analyses) > 1:
                        try:
                            comparative_prompt = VideoFrameAnalysisPrompts.get_comparative_frame_analysis_prompt(
                                frames_data=extracted_frames
                            )
                            comparative_analysis = {
                                "prompt": comparative_prompt,
                                "frame_count": len(extracted_frames),
                                "analysis_status": "prompt_generated"
                            }
                        except Exception as comp_error:
                            logger.warning(f"Failed to generate comparative analysis: {comp_error}")
                    
                    # Generate video summary prompt if requested
                    video_summary_prompt = None
                    if generate_video_summary:
                        try:
                            # Create mock frame analyses for summary generation
                            mock_frame_analyses = []
                            for frame in extracted_frames:
                                mock_analysis = {
                                    "timestamp": frame.get("timestamp", 0),
                                    "frame_number": frame.get("frame_number", 1),
                                    "analysis": {
                                        "scene_overview": {"pending": "Analysis would be performed by image analysis service"},
                                        "objects": [],
                                        "people": {"count": 0, "individuals": []},
                                        "environment": {},
                                        "technical_composition": {},
                                        "text_content": {},
                                        "activity_indicators": {},
                                        "contextual_clues": {},
                                        "emotional_aesthetic": {},
                                        "technical_observations": {}
                                    }
                                }
                                mock_frame_analyses.append(mock_analysis)
                            
                            video_summary_prompt = VideoFrameAnalysisPrompts.get_video_summary_prompt(
                                frame_analyses=mock_frame_analyses,
                                video_info={
                                    "duration": frames_data.get("video_info", {}).get("duration", 0),
                                    "source": video_info["value"]
                                }
                            )
                        except Exception as summary_error:
                            logger.warning(f"Failed to generate video summary prompt: {summary_error}")
                    
                    # Compile results for this video
                    video_analysis = {
                        "video_source": video_info["value"],
                        "video_type": video_info["type"],
                        "extraction_info": {
                            "total_frames_extracted": len(extracted_frames),
                            "frame_interval": frame_interval,
                            "segment_duration": frames_data.get("extraction_config", {}).get("segment_duration", 0),
                            "output_directory": frames_data.get("output_directory")
                        },
                        "frame_analyses": frame_analyses,
                        "comparative_analysis": comparative_analysis,
                        "video_summary_prompt": video_summary_prompt,
                        "analysis_metadata": {
                            "analysis_focus": analysis_focus,
                            "frame_count": len(frame_analyses),
                            "analysis_timestamp": datetime.utcnow().isoformat()
                        }
                    }
                    
                    all_analysis_results.append(video_analysis)
                    processing_summary.append({
                        "video": video_info["value"],
                        "status": "success",
                        "frames_extracted": len(extracted_frames),
                        "frames_analyzed": len(frame_analyses)
                    })
                    
                except Exception as video_error:
                    logger.error(f"Failed to process video {video_info['value']}: {video_error}")
                    processing_summary.append({
                        "video": video_info["value"],
                        "status": "failed",
                        "error": str(video_error)
                    })
                    continue
            
            # Compile final response
            response_data = {
                "success": True,
                "analysis_type": "comprehensive_video_content_analysis",
                "processing_summary": {
                    "total_videos": len(videos_to_process),
                    "successful_videos": len([s for s in processing_summary if s["status"] == "success"]),
                    "failed_videos": len([s for s in processing_summary if s["status"] == "failed"]),
                    "details": processing_summary
                },
                "analysis_results": all_analysis_results,
                "configuration": {
                    "segment_start": segment_start,
                    "segment_end": segment_end,
                    "frame_interval": frame_interval,
                    "max_frames_per_video": max_frames_per_video,
                    "analysis_focus": analysis_focus,
                    "include_comparative_analysis": include_comparative_analysis,
                    "generate_video_summary": generate_video_summary
                },
                "usage_notes": [
                    "This tool extracts frames and generates comprehensive analysis prompts",
                    "For actual image analysis, send the generated prompts to an image analysis service",
                    "Frame images are saved locally in the output directories specified",
                    "Use the comparative analysis and video summary prompts for deeper insights"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save results to resource manager if any videos were processed successfully
            if all_analysis_results:
                try:
                    resource_uri = self.resource_manager.save_visualization(
                        viz_type="video_content_analysis",
                        viz_data=response_data
                    )
                    response_data["resource_uri"] = resource_uri
                    response_data["saved_to_session"] = True
                    
                    current_session = self.resource_manager.get_session()
                    if current_session:
                        response_data["session_info"] = {
                            "session_id": current_session.session_id,
                            "session_title": current_session.title
                        }
                    
                except Exception as save_error:
                    logger.warning(f"Failed to save analysis results: {save_error}")
                    response_data["resource_save_error"] = str(save_error)
                    response_data["saved_to_session"] = False
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Video content analysis failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Comprehensive video content analysis failed",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _generate_dashboard_artifact_prompt(
        self,
        session_id: Optional[str] = None,
        include_video_analysis: bool = True,
        include_engagement_metrics: bool = True,
        dashboard_title: str = "YouTube Analytics Dashboard",
        auto_generate: bool = True
    ) -> List[TextContent]:
        """Generate interactive HTML dashboard artifact prompt from session data."""
        logger.info(f"Generating dashboard artifact prompt for session: {session_id or 'current'}")
        
        try:
            # Get session data
            session = self.resource_manager.get_session(session_id)
            
            if not session:
                if session_id:
                    error_msg = f"Session '{session_id}' not found"
                else:
                    error_msg = "No current session is active"
                    
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": error_msg,
                        "message": "Cannot generate dashboard without active session",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Prepare session data
            session_data = {
                "session_id": session.session_id,
                "session_title": session.title,
                "title": dashboard_title,
                "video_count": len(session.video_ids),
                "total_video_ids": len(session.video_ids),
                "timestamp": datetime.utcnow().isoformat(),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "description": session.description
            }
            
            # Collect visualization results from session resources
            visualization_results = []
            video_analysis_data = None
            engagement_data = None
            
            for resource_uri in session.resources:
                try:
                    # Extract resource type from URI
                    if not resource_uri.startswith("youtube://"):
                        continue
                    
                    parts = resource_uri[10:].split('/')
                    if len(parts) != 2:
                        continue
                    
                    resource_type, resource_id = parts
                    
                    # Load visualization resources
                    if resource_type == 'visualization':
                        # Load the visualization metadata
                        metadata_loaded = False
                        resource_data = {}
                        
                        # Search for the visualization metadata file
                        for session_dir in self.resource_manager.visualizations_path.iterdir():
                            if session_dir.is_dir():
                                viz_dir = session_dir / resource_id
                                if viz_dir.exists():
                                    metadata_file = viz_dir / "metadata.json"
                                    if metadata_file.exists():
                                        with open(metadata_file, 'r') as f:
                                            viz_metadata = json.load(f)
                                        resource_data = viz_metadata.get('data', {})
                                        metadata_loaded = True
                                        break
                        
                        if metadata_loaded:
                            viz_result = {
                                'type': f"visualization_{viz_metadata.get('viz_type', 'unknown') or 'unknown'}",
                                'success': resource_data.get('success', False),
                                'data': resource_data,
                                'timestamp': viz_metadata.get('timestamp'),
                                'resource_uri': resource_uri,
                                'viz_type': viz_metadata.get('viz_type', '') or ''
                            }
                            
                            # Extract specific visualization data
                            if resource_data.get('success'):
                                viz_result.update({
                                    'chart_type': resource_data.get('chart_type'),
                                    'data_points': resource_data.get('data_points'),
                                    'total_views': resource_data.get('total_views'),
                                    'max_value': resource_data.get('max_value'),
                                    'file_path': resource_data.get('file_path')
                                })
                            
                            visualization_results.append(viz_result)
                            
                            # Check for specific analysis types
                            viz_type = viz_metadata.get('viz_type', '') or ''  # Ensure it's always a string
                            if include_video_analysis and viz_type and 'video_content_analysis' in viz_type.lower():
                                video_analysis_data = resource_data
                            elif include_engagement_metrics and viz_type and 'engagement' in viz_type.lower():
                                engagement_data = resource_data
                    
                except Exception as e:
                    logger.warning(f"Failed to load resource {resource_uri}: {e}")
                    continue
            
            # Generate the dashboard prompt
            dashboard_prompt = dashboard_prompt_generator.generate_visualization_dashboard_prompt(
                session_data=session_data,
                visualization_results=visualization_results,
                video_analysis_data=video_analysis_data,
                engagement_data=engagement_data
            )
            
            # Prepare response
            response_data = {
                "success": True,
                "session_id": session.session_id,
                "session_title": session.title,
                "dashboard_title": dashboard_title,
                "visualization_count": len(visualization_results),
                "has_video_analysis": video_analysis_data is not None,
                "has_engagement_data": engagement_data is not None,
                "dashboard_prompt": dashboard_prompt,
                "message": f"Dashboard artifact prompt generated for session '{session.title}'",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add auto-generation instruction if requested
            if auto_generate:
                response_data["instruction"] = "Please create an HTML artifact using the dashboard_prompt provided above. This will generate a complete interactive analytics dashboard."
                response_data["next_step"] = "artifact_generation"
            
            # Save the prompt as a resource
            try:
                prompt_uri = self.resource_manager.save_visualization(
                    viz_type="dashboard_prompt",
                    viz_data={
                        "prompt": dashboard_prompt,
                        "session_data": session_data,
                        "auto_generate": auto_generate
                    },
                    session_id=session.session_id
                )
                response_data["prompt_resource_uri"] = prompt_uri
                
            except Exception as save_error:
                logger.warning(f"Failed to save dashboard prompt as resource: {save_error}")
                response_data["resource_save_error"] = str(save_error)
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard artifact prompt: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to generate dashboard artifact prompt",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _analyze_video_frames_with_ai(
        self,
        video_id: str,
        frame_paths: Optional[List[str]] = None,
        analysis_focus: List[str] = None,
        generate_video_summary: bool = True,
        max_frames_to_analyze: int = 10
    ) -> List[TextContent]:
        """Analyze extracted video frames using comprehensive AI prompts."""
        logger.info(f"Starting AI-powered frame analysis for video: {video_id}")
        
        try:
            # Auto-detect frame paths if not provided
            if not frame_paths:
                # Look for extracted frames in the cache directory
                frame_dir = self.frame_extractor.frames_dir / f"frames_{video_id}"
                if frame_dir.exists():
                    frame_files = list(frame_dir.glob("*.jpg")) + list(frame_dir.glob("*.png"))
                    frame_paths = [str(f) for f in sorted(frame_files)[:max_frames_to_analyze]]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": f"No extracted frames found for video {video_id}",
                            "message": "Please extract frames first using the extract_video_frames tool",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    )]
            
            if not frame_paths:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "No frame paths provided or found",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            # Limit frames to analyze
            frames_to_analyze = frame_paths[:max_frames_to_analyze]
            
            # Generate comprehensive analysis prompts for each frame
            frame_analysis_prompts = []
            
            for i, frame_path in enumerate(frames_to_analyze):
                if not Path(frame_path).exists():
                    logger.warning(f"Frame file not found: {frame_path}")
                    continue
                
                # Extract frame metadata from filename or path
                frame_info = {
                    "frame_number": i + 1,
                    "file_path": frame_path,
                    "timestamp": i * 1.0,  # Estimate timestamp
                    "time_formatted": f"{int(i * 1.0 // 60):02d}:{int(i * 1.0 % 60):02d}"
                }
                
                # Generate comprehensive analysis prompt
                analysis_prompt = VideoFrameAnalysisPrompts.get_comprehensive_frame_analysis_prompt(
                    frame_info=frame_info,
                    analysis_focus=analysis_focus
                )
                
                frame_analysis_prompts.append({
                    "frame_number": i + 1,
                    "frame_path": frame_path,
                    "frame_info": frame_info,
                    "analysis_prompt": analysis_prompt
                })
            
            # Generate video summary prompt if requested
            video_summary_prompt = ""
            if generate_video_summary:
                # Mock frame analyses for summary prompt (in real implementation, these would be actual AI responses)
                mock_frame_analyses = []
                for prompt_data in frame_analysis_prompts:
                    mock_frame_analyses.append({
                        "timestamp": prompt_data["frame_info"]["timestamp"],
                        "frame_number": prompt_data["frame_info"]["frame_number"],
                        "analysis": "Frame analysis would be provided by AI here"
                    })
                
                video_info = {
                    "duration": len(frames_to_analyze) * 1.0,
                    "video_id": video_id
                }
                
                video_summary_prompt = VideoFrameAnalysisPrompts.get_video_summary_prompt(
                    frame_analyses=mock_frame_analyses,
                    video_info=video_info
                )
            
            # Prepare response with all analysis prompts
            response_data = {
                "success": True,
                "video_id": video_id,
                "frames_analyzed": len(frame_analysis_prompts),
                "total_frames_found": len(frame_paths),
                "analysis_prompts": frame_analysis_prompts,
                "video_summary_prompt": video_summary_prompt if generate_video_summary else None,
                "instructions": {
                    "individual_frame_analysis": "Use the analysis_prompt for each frame to get detailed AI analysis of that specific frame",
                    "video_summary": "Use the video_summary_prompt to generate a comprehensive video content summary" if generate_video_summary else None,
                    "implementation_note": "In a real implementation, you would send each frame image along with its analysis_prompt to an AI vision model"
                },
                "message": f"Generated comprehensive AI analysis prompts for {len(frame_analysis_prompts)} frames",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response_data, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"AI frame analysis failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to generate AI frame analysis prompts",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    # Advanced Trimming Tool Handlers
    
    async def _smart_trim_video(
        self,
        video_url: str,
        trim_instructions: str,
        output_format: str = "mp4",
        quality: str = "high",
        include_audio: bool = True
    ) -> List[TextContent]:
        """Handle smart video trimming with AI-powered analysis."""
        logger.info(f"Smart trimming video: {video_url} with instructions: {trim_instructions}")
        
        try:
            if not ADVANCED_TRIMMING_AVAILABLE:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Advanced trimming features not available",
                        "message": "Required dependencies for advanced trimming are not installed",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            result = await self.advanced_trimming.smart_trim_video(
                video_url=video_url,
                trim_instructions=trim_instructions,
                output_format=output_format,
                quality=quality,
                include_audio=include_audio
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Smart video trimming failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Smart video trimming failed",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _detect_video_scenes(
        self,
        video_url: str,
        detection_method: str = "combined",
        scene_threshold: float = 0.3
    ) -> List[TextContent]:
        """Handle video scene detection."""
        logger.info(f"Detecting scenes in video: {video_url} using method: {detection_method}")
        
        try:
            if not ADVANCED_TRIMMING_AVAILABLE:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Advanced trimming features not available",
                        "message": "Required dependencies for scene detection are not installed",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            result = await self.advanced_trimming.detect_video_scenes(
                video_url=video_url,
                detection_method=detection_method,
                scene_threshold=scene_threshold
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Video scene detection failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Video scene detection failed",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _analyze_audio_patterns(
        self,
        video_url: str,
        target_patterns: Optional[List[str]] = None,
        include_transcription: bool = True
    ) -> List[TextContent]:
        """Handle audio pattern analysis."""
        logger.info(f"Analyzing audio patterns in video: {video_url}")
        
        try:
            if not ADVANCED_TRIMMING_AVAILABLE:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Advanced trimming features not available",
                        "message": "Required dependencies for audio analysis are not installed",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            result = await self.advanced_trimming.analyze_audio_patterns(
                video_url=video_url,
                target_patterns=target_patterns,
                include_transcription=include_transcription
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Audio pattern analysis failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Audio pattern analysis failed",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
    
    async def _extract_content_segments(
        self,
        video_url: str,
        segment_criteria: Dict[str, Any],
        output_dir: str,
        context_window: float = 2.0
    ) -> List[TextContent]:
        """Handle content-based segment extraction."""
        logger.info(f"Extracting content segments from video: {video_url}")
        
        try:
            if not ADVANCED_TRIMMING_AVAILABLE:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Advanced trimming features not available",
                        "message": "Required dependencies for content extraction are not installed",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                )]
            
            result = await self.advanced_trimming.extract_content_segments(
                video_url=video_url,
                segment_criteria=segment_criteria,
                output_dir=output_dir,
                context_window=context_window
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
            
        except Exception as e:
            logger.error(f"Content segment extraction failed: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Content segment extraction failed",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]