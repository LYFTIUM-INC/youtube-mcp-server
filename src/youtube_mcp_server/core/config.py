"""
Configuration management for YouTube MCP server.

Adapted from existing config.py with MCP-specific enhancements.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class YouTubeMCPConfig(BaseSettings):
    """
    Main configuration for YouTube MCP Server.
    
    Adapted from existing config.py with Pydantic validation and MCP enhancements.
    """
    
    # API Keys
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY") 
    service_account_file: Optional[str] = Field(None, env="SERVICE_ACCOUNT_FILE")
    
    # YouTube API Configuration
    youtube_api_quota_limit: int = Field(10000, description="Daily YouTube API quota limit")
    youtube_api_rate_limit: float = Field(1.0, description="Requests per second")
    
    # Cache Configuration
    cache_directory: str = Field("youtube_cache", description="Directory for caching data")
    cache_ttl_seconds: int = Field(3600, description="Cache TTL in seconds")
    
    # Download Configuration
    download_directory: str = Field("downloads", description="Directory for downloaded files")
    output_directory: str = Field("output", description="Base directory for all output files")
    max_concurrent_downloads: int = Field(3, description="Maximum concurrent downloads")
    
    # Rate Limiting
    rate_limit_tokens_per_second: float = Field(1.0, description="Rate limit tokens per second")
    rate_limit_bucket_size: int = Field(10, description="Rate limit bucket size")
    
    # Retry Configuration
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_base_delay: float = Field(1.0, description="Base delay for retries")
    retry_max_delay: float = Field(60.0, description="Maximum delay for retries")
    
    # Logging Configuration
    logging_level: str = Field("INFO", description="Logging level")
    logging_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format"
    )
    
    # Server Configuration
    server_host: str = Field("localhost", description="MCP server host")
    server_port: int = Field(8000, description="MCP server port")
    server_debug: bool = Field(False, description="Enable debug mode")
    
    # Feature Flags
    enable_caching: bool = Field(True, description="Enable caching")
    enable_rate_limiting: bool = Field(True, description="Enable rate limiting")
    enable_analytics: bool = Field(True, description="Enable analytics features")
    enable_downloads: bool = Field(True, description="Enable video downloads")
    enable_advanced_trimming: bool = Field(True, description="Enable advanced trimming features")
    
    # Advanced Trimming Configuration
    whisper_model_size: str = Field("base", description="Whisper model size (tiny, base, small, medium, large)")
    scene_detection_threshold: float = Field(0.3, description="Scene detection sensitivity threshold")
    audio_confidence_threshold: float = Field(0.8, description="Audio classification confidence threshold")
    enable_gpu_acceleration: bool = Field(True, description="Enable GPU acceleration for AI models")
    enable_scene_detection: bool = Field(True, description="Enable computer vision scene detection")
    enable_audio_analysis: bool = Field(True, description="Enable audio pattern recognition")
    max_video_length_for_analysis: int = Field(3600, description="Maximum video length for analysis (seconds)")
    temp_processing_dir: str = Field("temp_processing", description="Directory for temporary processing files")
    model_cache_dir: str = Field("model_cache", description="Directory for cached AI models")
    
    # Data Processing
    max_comments_per_video: int = Field(100, description="Maximum comments to fetch per video")
    max_videos_per_search: int = Field(50, description="Maximum videos per search")
    
    # Security
    allowed_domains: List[str] = Field(
        default_factory=lambda: ["youtube.com", "youtu.be"],
        description="Allowed domains for video URLs"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables
        
    @validator("service_account_file")
    def validate_service_account_file(cls, v):
        """Validate that service account file exists if provided."""
        if v and not Path(v).exists():
            # Only warn if explicitly set, ignore if from environment
            pass
        return v
    
    @validator("logging_level")
    def validate_logging_level(cls, v):
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    def model_post_init(self, __context) -> None:
        """Post-initialization setup."""
        self._load_environment()
        self._validate_configuration()
        self._setup_logging()
    
    def _load_environment(self) -> None:
        """Load environment variables from multiple locations."""
        env_paths = [
            Path('.env'),
            Path('../.env'),
            Path(__file__).parent.parent.parent.parent / '.env',
            Path(__file__).parent.parent.parent.parent.parent / '.env',
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                break
    
    def _validate_configuration(self) -> None:
        """Validate the configuration."""
        # Check API keys
        if not self.google_api_key and not self.service_account_file:
            logger.warning("Neither GOOGLE_API_KEY nor SERVICE_ACCOUNT_FILE is configured")
        
        if self.google_api_key:
            logger.info(f"Google API key configured: {self.google_api_key[:8]}...")
        
        if self.service_account_file and Path(self.service_account_file).exists():
            logger.info(f"Service account file: {self.service_account_file}")
        
        # Create directories
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)
        Path(self.download_directory).mkdir(parents=True, exist_ok=True)
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        Path(self.temp_processing_dir).mkdir(parents=True, exist_ok=True)
        Path(self.model_cache_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # For MCP servers, send logs to stderr and reduce verbosity
        import sys
        logging.basicConfig(
            level=logging.WARNING,  # Reduce logging for MCP
            format=self.logging_format,
            stream=sys.stderr,  # Ensure logs go to stderr
            force=True
        )
    
    def get_youtube_api_config(self) -> Dict[str, Any]:
        """Get YouTube API configuration."""
        return {
            "api_key": self.google_api_key,
            "service_account_file": self.service_account_file,
            "quota_limit": self.youtube_api_quota_limit,
            "rate_limit": self.youtube_api_rate_limit,
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "cache_dir": self.cache_directory,
            "ttl_seconds": self.cache_ttl_seconds,
            "enabled": self.enable_caching,
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "tokens_per_second": self.rate_limit_tokens_per_second,
            "bucket_size": self.rate_limit_bucket_size,
            "enabled": self.enable_rate_limiting,
        }
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration."""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.retry_base_delay,
            "max_delay": self.retry_max_delay,
        }
    
    def get_download_config(self) -> Dict[str, Any]:
        """Get download configuration."""
        return {
            "download_dir": self.download_directory,
            "max_concurrent": self.max_concurrent_downloads,
            "enabled": self.enable_downloads,
        }
    
    def get_advanced_trimming_config(self) -> Dict[str, Any]:
        """Get advanced trimming configuration."""
        return {
            "enabled": self.enable_advanced_trimming,
            "whisper_model_size": self.whisper_model_size,
            "scene_detection_threshold": self.scene_detection_threshold,
            "audio_confidence_threshold": self.audio_confidence_threshold,
            "enable_gpu_acceleration": self.enable_gpu_acceleration,
            "enable_scene_detection": self.enable_scene_detection,
            "enable_audio_analysis": self.enable_audio_analysis,
            "max_video_length": self.max_video_length_for_analysis,
            "temp_processing_dir": self.temp_processing_dir,
            "model_cache_dir": self.model_cache_dir,
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return {
            "host": self.server_host,
            "port": self.server_port,
            "debug": self.server_debug,
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_flags = {
            "caching": self.enable_caching,
            "rate_limiting": self.enable_rate_limiting,
            "analytics": self.enable_analytics,
            "downloads": self.enable_downloads,
            "advanced_trimming": self.enable_advanced_trimming,
            "scene_detection": self.enable_scene_detection,
            "audio_analysis": self.enable_audio_analysis,
            "gpu_acceleration": self.enable_gpu_acceleration,
        }
        return feature_flags.get(feature, False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()


# Legacy Config class for backward compatibility
class Config:
    """Legacy configuration class for backward compatibility."""
    
    def __init__(self):
        # Create the new config
        self._config = YouTubeMCPConfig()
        
        # Set legacy attributes
        self.google_api_key = self._config.google_api_key
        self.GOOGLE_API_KEY = self.google_api_key
        self.service_account_file = self._config.service_account_file
        self.SERVICE_ACCOUNT_FILE = self.service_account_file
        self.organization_id = os.getenv("ORGANIZATION_ID", "")
        self.project_id = os.getenv("PROJECT_ID", "")
        
        # NLP Models (for backward compatibility)
        self.SPACY_MODEL = "en_core_web_sm"
        self.NLTK_RESOURCES = ["punkt", "averaged_perceptron_tagger", "stopwords"]
        
        # Logging (legacy)
        self.LOGGING_LEVEL = self._config.logging_level
        self.LOGGING_FORMAT = self._config.logging_format
        
        # Visualization Config (legacy)
        self.MAX_OPEN_FIGURES = 150


# Global configuration instance
config = YouTubeMCPConfig()


def get_config() -> YouTubeMCPConfig:
    """Get the global configuration instance."""
    return config


def reload_config() -> YouTubeMCPConfig:
    """Reload the configuration."""
    global config
    config = YouTubeMCPConfig()
    return config