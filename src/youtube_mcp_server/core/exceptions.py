"""
Exception classes for YouTube MCP Server.

Provides comprehensive error handling with specific exception types for different
failure scenarios, enabling proper error recovery and user feedback.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class YouTubeMCPError(Exception):
    """Base exception class for all YouTube MCP Server errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
    ):
        """
        Initialize YouTubeMCPError.
        
        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            details: Additional error details.
            recoverable: Whether the error is potentially recoverable.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Code: {self.error_code}, Details: {self.details})"
        return f"{self.message} (Code: {self.error_code})"


class ConfigurationError(YouTubeMCPError):
    """Raised when there are configuration issues."""
    
    def __init__(self, message: str, config_section: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if config_section:
            details["config_section"] = config_section
        
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details,
            recoverable=False,
            **kwargs
        )


class AuthenticationError(YouTubeMCPError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if auth_type:
            details["auth_type"] = auth_type
        
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            details=details,
            recoverable=False,
            **kwargs
        )


class ValidationError(YouTubeMCPError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if expected_type:
            details["expected_type"] = expected_type
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            recoverable=True,
            **kwargs
        )


class YouTubeAPIError(YouTubeMCPError):
    """Base class for YouTube API-related errors."""
    
    def __init__(
        self,
        message: str,
        api_error_code: Optional[str] = None,
        http_status: Optional[int] = None,
        quota_cost: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if api_error_code:
            details["api_error_code"] = api_error_code
        if http_status:
            details["http_status"] = http_status
        if quota_cost:
            details["quota_cost"] = quota_cost
        
        super().__init__(
            message=message,
            error_code="YOUTUBE_API_ERROR",
            details=details,
            **kwargs
        )


class QuotaExceededError(YouTubeAPIError):
    """Raised when YouTube API quota is exceeded."""
    
    def __init__(
        self,
        message: str = "YouTube API quota exceeded",
        reset_time: Optional[datetime] = None,
        quota_used: Optional[int] = None,
        quota_limit: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if reset_time:
            details["reset_time"] = reset_time.isoformat()
        if quota_used:
            details["quota_used"] = quota_used
        if quota_limit:
            details["quota_limit"] = quota_limit
        
        self.reset_time = reset_time
        self.quota_used = quota_used
        self.quota_limit = quota_limit
        
        super().__init__(
            message=message,
            api_error_code="quotaExceeded",
            details=details,
            recoverable=True,
            **kwargs
        )


class RateLimitExceededError(YouTubeAPIError):
    """Raised when YouTube API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "YouTube API rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        self.retry_after = retry_after
        
        super().__init__(
            message=message,
            api_error_code="rateLimitExceeded",
            details=details,
            recoverable=True,
            **kwargs
        )


class VideoNotFoundError(YouTubeAPIError):
    """Raised when a requested video is not found or not accessible."""
    
    def __init__(self, video_id: str, **kwargs):
        self.video_id = video_id
        
        details = kwargs.pop("details", {})
        details["video_id"] = video_id
        
        super().__init__(
            message=f"Video not found or not accessible: {video_id}",
            api_error_code="videoNotFound",
            details=details,
            recoverable=False,
            **kwargs
        )


class ChannelNotFoundError(YouTubeAPIError):
    """Raised when a requested channel is not found or not accessible."""
    
    def __init__(self, channel_id: str, **kwargs):
        self.channel_id = channel_id
        
        details = kwargs.pop("details", {})
        details["channel_id"] = channel_id
        
        super().__init__(
            message=f"Channel not found or not accessible: {channel_id}",
            api_error_code="channelNotFound",
            details=details,
            recoverable=False,
            **kwargs
        )


class TranscriptNotAvailableError(YouTubeAPIError):
    """Raised when video transcript is not available."""
    
    def __init__(self, video_id: str, languages: Optional[List[str]] = None, **kwargs):
        self.video_id = video_id
        self.languages = languages or []
        
        details = kwargs.pop("details", {})
        details["video_id"] = video_id
        details["requested_languages"] = self.languages
        
        message = f"Transcript not available for video: {video_id}"
        if languages:
            message += f" (requested languages: {', '.join(languages)})"
        
        super().__init__(
            message=message,
            api_error_code="transcriptNotAvailable",
            details=details,
            recoverable=False,
            **kwargs
        )


class CacheError(YouTubeMCPError):
    """Raised when cache operations fail."""
    
    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            recoverable=True,
            **kwargs
        )


class AnalysisError(YouTubeMCPError):
    """Raised when data analysis operations fail."""
    
    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        data_size: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if analysis_type:
            details["analysis_type"] = analysis_type
        if data_size:
            details["data_size"] = data_size
        
        super().__init__(
            message=message,
            error_code="ANALYSIS_ERROR",
            details=details,
            recoverable=True,
            **kwargs
        )


class MLModelError(AnalysisError):
    """Raised when machine learning model operations fail."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if model_name:
            details["model_name"] = model_name
        if model_version:
            details["model_version"] = model_version
        
        super().__init__(
            message=message,
            analysis_type="machine_learning",
            error_code="ML_MODEL_ERROR",
            details=details,
            **kwargs
        )


class ComputerVisionError(AnalysisError):
    """Raised when computer vision operations fail."""
    
    def __init__(
        self,
        message: str,
        image_url: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if image_url:
            details["image_url"] = image_url
        if operation:
            details["cv_operation"] = operation
        
        super().__init__(
            message=message,
            analysis_type="computer_vision",
            error_code="CV_ERROR",
            details=details,
            **kwargs
        )


class TextAnalysisError(AnalysisError):
    """Raised when text analysis operations fail."""
    
    def __init__(
        self,
        message: str,
        text_length: Optional[int] = None,
        language: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if text_length:
            details["text_length"] = text_length
        if language:
            details["language"] = language
        
        super().__init__(
            message=message,
            analysis_type="text_analysis",
            error_code="TEXT_ANALYSIS_ERROR",
            details=details,
            **kwargs
        )


class DownloadError(YouTubeMCPError):
    """Raised when video download operations fail."""
    
    def __init__(
        self,
        message: str,
        video_id: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if video_id:
            details["video_id"] = video_id
        if url:
            details["url"] = url
        
        super().__init__(
            message=message,
            error_code="DOWNLOAD_ERROR",
            details=details,
            **kwargs
        )


class ExportError(YouTubeMCPError):
    """Raised when data export operations fail."""
    
    def __init__(
        self,
        message: str,
        export_format: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if export_format:
            details["export_format"] = export_format
        if file_path:
            details["file_path"] = file_path
        
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            details=details,
            **kwargs
        )


class NetworkError(YouTubeMCPError):
    """Raised when network operations fail."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details,
            **kwargs
        )


class TimeoutError(YouTubeMCPError):
    """Raised when operations timeout."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details=details,
            recoverable=True,
            **kwargs
        )


class ResourceNotFoundError(YouTubeMCPError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
            recoverable=False,
            **kwargs
        )


# Error code mappings for YouTube API errors
YOUTUBE_API_ERROR_MAPPING = {
    "quotaExceeded": QuotaExceededError,
    "rateLimitExceeded": RateLimitExceededError,
    "videoNotFound": VideoNotFoundError,
    "channelNotFound": ChannelNotFoundError,
    "forbidden": AuthenticationError,
    "unauthorized": AuthenticationError,
    "badRequest": ValidationError,
}


def create_youtube_api_error(
    error_code: str,
    message: str,
    **kwargs
) -> YouTubeAPIError:
    """
    Create appropriate YouTube API error based on error code.
    
    Args:
        error_code: YouTube API error code.
        message: Error message.
        **kwargs: Additional error details.
        
    Returns:
        Appropriate YouTubeAPIError subclass instance.
    """
    error_class = YOUTUBE_API_ERROR_MAPPING.get(error_code, YouTubeAPIError)
    return error_class(message, api_error_code=error_code, **kwargs)


def handle_http_error(http_status: int, message: str, **kwargs) -> YouTubeMCPError:
    """
    Create appropriate error based on HTTP status code.
    
    Args:
        http_status: HTTP status code.
        message: Error message.
        **kwargs: Additional error details.
        
    Returns:
        Appropriate error instance.
    """
    if http_status == 400:
        return ValidationError(message, **kwargs)
    elif http_status == 401:
        return AuthenticationError(message, **kwargs)
    elif http_status == 403:
        return QuotaExceededError(message, **kwargs)
    elif http_status == 404:
        return ResourceNotFoundError(message, **kwargs)
    elif http_status == 429:
        return RateLimitExceededError(message, **kwargs)
    elif 500 <= http_status < 600:
        return NetworkError(message, status_code=http_status, **kwargs)
    else:
        return YouTubeMCPError(message, error_code=f"HTTP_{http_status}", **kwargs)


# Exception context manager for error handling
class ErrorContext:
    """Context manager for standardized error handling."""
    
    def __init__(
        self,
        operation: str,
        reraise: bool = True,
        default_return: Any = None,
        logger = None,
    ):
        """
        Initialize error context.
        
        Args:
            operation: Description of the operation being performed.
            reraise: Whether to reraise caught exceptions.
            default_return: Default return value if error occurs and reraise=False.
            logger: Logger instance for error logging.
        """
        self.operation = operation
        self.reraise = reraise
        self.default_return = default_return
        self.logger = logger
        self.error: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            
            # Log error if logger provided
            if self.logger:
                self.logger.error(f"Error in {self.operation}: {exc_val}")
            
            # Convert to YouTubeMCPError if needed
            if not isinstance(exc_val, YouTubeMCPError):
                wrapped_error = YouTubeMCPError(
                    message=f"Error in {self.operation}: {exc_val}",
                    details={"operation": self.operation, "original_error": str(exc_val)},
                )
                
                if self.reraise:
                    raise wrapped_error from exc_val
            elif self.reraise:
                raise exc_val
            
            # Don't reraise if reraise=False
            return not self.reraise
        
        return False


# Utility functions for error handling
def is_recoverable_error(error: Exception) -> bool:
    """Check if an error is potentially recoverable."""
    if isinstance(error, YouTubeMCPError):
        return error.recoverable
    
    # Default assumption for unknown errors
    return True


def get_error_severity(error: Exception) -> str:
    """Get error severity level."""
    if isinstance(error, (ConfigurationError, AuthenticationError)):
        return "critical"
    elif isinstance(error, (QuotaExceededError, RateLimitExceededError)):
        return "warning"
    elif isinstance(error, (ValidationError, ResourceNotFoundError)):
        return "info"
    else:
        return "error"


def format_error_for_user(error: Exception) -> Dict[str, Any]:
    """Format error for user-friendly display."""
    if isinstance(error, YouTubeMCPError):
        return {
            "error": True,
            "message": error.message,
            "code": error.error_code,
            "recoverable": error.recoverable,
            "details": error.details,
        }
    else:
        return {
            "error": True,
            "message": str(error),
            "code": "UNKNOWN_ERROR",
            "recoverable": True,
        }