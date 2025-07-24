"""
YouTube API client for MCP server integration.

Adapted from the existing data_collection.py implementation with MCP-specific enhancements.
"""

import logging
import re
from typing import Dict, Optional, List, Any, Tuple
import asyncio
from datetime import datetime
import time
import random

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel, ValidationError, Field

from ..core.config import Config
from ..infrastructure.cache_manager import ErrorHandler
from ..infrastructure.cache_manager import CacheManager
from ..infrastructure.rate_limiter import RateLimiter
from ..infrastructure.retry_manager import RetryManager
from ..core.exceptions import (
    YouTubeAPIError,
    QuotaExceededError,
    VideoNotFoundError,
    ConfigurationError
)


class VideoMetadata(BaseModel):
    """Video metadata model."""
    video_id: str
    subject: str = ""
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    url: str
    view_count: Optional[int] = Field(None, ge=0)
    like_count: Optional[int] = Field(None, ge=0)
    comment_count: Optional[int] = Field(None, ge=0)
    upload_date: str
    thumbnail_url: str
    duration: Optional[str] = None
    channel_id: str = ""
    channel_title: str = ""
    category_id: Optional[str] = None
    next_page_token: Optional[str] = None
    time_stamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Comment(BaseModel):
    """Comment model."""
    author: str
    text: str
    like_count: int
    reply_count: Optional[int] = Field(None, ge=0)
    published_at: str
    updated_at: Optional[str] = None
    parent_id: Optional[str] = None
    comment_id: str


class Transcript(BaseModel):
    """Transcript segment model."""
    start: float
    end: float
    text: str
    duration: Optional[float] = None


class ChannelInfo(BaseModel):
    """Channel information model."""
    channel_id: str
    title: str
    description: str
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    country: Optional[str] = None
    published_at: str
    thumbnail_url: str
    custom_url: Optional[str] = None


class SearchResult(BaseModel):
    """Search result model."""
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    thumbnail_url: str
    description: str


class YouTubeAPIClient:
    """
    YouTube API client with caching, rate limiting, and error handling.
    
    Adapted from existing data_collection.py with MCP server enhancements.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_manager=None, rate_limiter=None, error_handler=None):
        """
        Initialize YouTube API client.
        
        Args:
            api_key: YouTube Data API key
            cache_manager: Cache manager instance
            rate_limiter: Rate limiter instance
            error_handler: Error handler instance
        """
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Use provided components or create defaults
        self.cache = cache_manager or CacheManager()
        self.rate_limiter = rate_limiter or RateLimiter(tokens_per_second=1.0, bucket_size=10)
        self.error_handler = error_handler or ErrorHandler()
        self.retry_manager = RetryManager(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0
        )
        
        # Initialize YouTube API client
        self._youtube = None
        
        self.logger.info("YouTubeAPIClient initialized successfully")
    
    async def initialize(self) -> None:
        """Initialize the YouTube API client."""
        try:
            if self.api_key:
                self._youtube = build('youtube', 'v3', developerKey=self.api_key)
                self.logger.info("YouTube API client initialized with API key")
            else:
                self.logger.warning("No API key provided - YouTube API calls will fail")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube API client: {e}")
            raise ConfigurationError(f"YouTube API initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Nothing specific to clean up for YouTube API client
        pass
    
    async def _make_api_call(self, operation_name: str, **kwargs) -> Any:
        """
        Make a rate-limited API call with retry logic.
        
        Args:
            operation_name: Name of the API operation
            **kwargs: Arguments for the API call
            
        Returns:
            API response data
        """
        # Check if YouTube client is initialized
        if self._youtube is None:
            raise ConfigurationError("YouTube API client not initialized. Call initialize() first.")
        
        await self.rate_limiter.acquire()
        
        async def _api_call():
            try:
                # Map operation names to API methods
                operations = {
                    'search': self._youtube.search().list,
                    'videos': self._youtube.videos().list,
                    'channels': self._youtube.channels().list,
                    'commentThreads': self._youtube.commentThreads().list,
                    'playlistItems': self._youtube.playlistItems().list,
                }
                
                if operation_name not in operations:
                    raise ValueError(f"Unknown operation: {operation_name}")
                
                # Execute API call
                request = operations[operation_name](**kwargs)
                response = request.execute()
                
                return response
                
            except HttpError as e:
                error_details = e.error_details[0] if e.error_details else {}
                error_reason = error_details.get('reason', 'unknown')
                
                if e.resp.status == 403 and 'quota' in error_reason.lower():
                    raise QuotaExceededError(f"YouTube API quota exceeded: {e}")
                elif e.resp.status == 404:
                    raise VideoNotFoundError(f"Resource not found: {e}")
                else:
                    raise YouTubeAPIError(f"YouTube API error: {e}")
            
            except Exception as e:
                raise YouTubeAPIError(f"Unexpected API error: {e}")
        
        return await self.retry_manager.execute_with_retry(_api_call)
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 10,
        order: str = "relevance",
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        region_code: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for videos on YouTube.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            order: Sort order (relevance, date, rating, viewCount, title)
            published_after: RFC 3339 timestamp
            published_before: RFC 3339 timestamp
            region_code: ISO 3166-1 alpha-2 country code
            
        Returns:
            List of search results
        """
        cache_key = f"search_{hash(f'{query}_{max_results}_{order}_{published_after}_{published_before}_{region_code}')}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return [SearchResult(**item) for item in cached_result]
        
        # Prepare API parameters
        params = {
            'part': 'snippet',
            'q': query,
            'maxResults': min(max_results, 50),
            'order': order,
            'type': 'video',
            'regionCode': region_code
        }
        
        if published_after:
            params['publishedAfter'] = published_after
        if published_before:
            params['publishedBefore'] = published_before
        
        # Make API call
        response = await self._make_api_call('search', **params)
        
        # Process results
        results = []
        for item in response.get('items', []):
            snippet = item['snippet']
            result = SearchResult(
                video_id=item['id']['videoId'],
                title=snippet['title'],
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                published_at=snippet['publishedAt'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                description=snippet['description']
            )
            results.append(result)
        
        # Cache results
        await self.cache.set(cache_key, [result.model_dump() for result in results])
        
        return results
    
    async def get_video_details(self, video_ids: List[str], parts: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get detailed information about videos.
        
        Args:
            video_ids: List of YouTube video IDs
            parts: List of parts to include (snippet, statistics, contentDetails)
            
        Returns:
            List of video data dictionaries
        """
        if parts is None:
            parts = ['snippet', 'statistics', 'contentDetails']
            
        # Convert list to comma-separated string
        video_ids_str = ','.join(video_ids)
        parts_str = ','.join(parts)
        
        cache_key = f"videos_{hash(video_ids_str)}_{hash(parts_str)}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Make API call
        response = await self._make_api_call(
            'videos',
            part=parts_str,
            id=video_ids_str
        )
        
        if not response.get('items'):
            return []
        
        results = []
        for item in response['items']:
            video_data = {
                'id': item['id'],
                'snippet': item.get('snippet', {}),
                'statistics': item.get('statistics', {}),
                'contentDetails': item.get('contentDetails', {})
            }
            results.append(video_data)
        
        # Cache result
        await self.cache.set(cache_key, results)
        
        return results
    
    def _normalize_username(self, username: str) -> str:
        """Normalize username by removing @ prefix if present."""
        if username.startswith('@'):
            return username[1:]
        return username
    
    async def get_channel_info(
        self, 
        channel_ids: Optional[List[str]] = None, 
        channel_usernames: Optional[List[str]] = None,
        parts: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get channel information.
        
        Args:
            channel_ids: List of YouTube channel IDs
            channel_usernames: List of YouTube channel usernames
            parts: List of parts to include
            
        Returns:
            List of channel data dictionaries
        """
        if not channel_ids and not channel_usernames:
            return []
            
        if parts is None:
            parts = ['snippet', 'statistics']
            
        parts_str = ','.join(parts)
        
        # Create cache key
        if channel_ids:
            cache_key = f"channels_ids_{hash(','.join(channel_ids))}_{hash(parts_str)}"
            api_params = {'id': ','.join(channel_ids)}
        else:
            # Normalize usernames (remove @ prefix if present)
            normalized_usernames = [self._normalize_username(username) for username in channel_usernames]
            cache_key = f"channels_usernames_{hash(','.join(normalized_usernames))}_{hash(parts_str)}"
            api_params = {'forUsername': ','.join(normalized_usernames)}
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Make API call
        response = await self._make_api_call(
            'channels',
            part=parts_str,
            **api_params
        )
        
        if not response.get('items'):
            return []
        
        results = []
        for item in response['items']:
            channel_data = {
                'id': item['id'],
                'snippet': item.get('snippet', {}),
                'statistics': item.get('statistics', {}),
                'contentDetails': item.get('contentDetails', {})
            }
            results.append(channel_data)
        
        # Cache result
        await self.cache.set(cache_key, results)
        
        return results
    
    async def get_video_comments(
        self, 
        video_id: str, 
        max_results: int = 100,
        order: str = "relevance",
        include_replies: bool = False,
        text_format: str = "plainText"
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a video.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to retrieve
            order: Sort order (time, relevance)
            
        Returns:
            List of comments
        """
        cache_key = f"comments_{video_id}_{max_results}_{order}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return [Comment(**comment) for comment in cached_result]
        
        comments = []
        next_page_token = None
        
        while len(comments) < max_results:
            # Calculate how many comments to fetch in this request
            remaining = max_results - len(comments)
            page_size = min(remaining, 100)  # API max is 100
            
            # Prepare API parameters
            params = {
                'part': 'snippet,replies',
                'videoId': video_id,
                'maxResults': page_size,
                'order': order
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                # Make API call
                response = await self._make_api_call('commentThreads', **params)
                
                # Process comments
                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    
                    comment = Comment(
                        author=snippet['authorDisplayName'],
                        text=snippet['textDisplay'],
                        like_count=snippet['likeCount'],
                        published_at=snippet['publishedAt'],
                        updated_at=snippet.get('updatedAt'),
                        comment_id=item['id']
                    )
                    comments.append(comment)
                    
                    # Add replies if present
                    if 'replies' in item:
                        for reply_item in item['replies']['comments']:
                            reply_snippet = reply_item['snippet']
                            reply = Comment(
                                author=reply_snippet['authorDisplayName'],
                                text=reply_snippet['textDisplay'],
                                like_count=reply_snippet['likeCount'],
                                published_at=reply_snippet['publishedAt'],
                                updated_at=reply_snippet.get('updatedAt'),
                                parent_id=item['id'],
                                comment_id=reply_item['id']
                            )
                            comments.append(reply)
                
                # Check for next page
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except YouTubeAPIError as e:
                if "commentsDisabled" in str(e):
                    self.logger.warning(f"Comments disabled for video {video_id}")
                    break
                else:
                    raise
        
        # Trim to exact count requested
        comments = comments[:max_results]
        
        # Convert to dictionaries for return
        comment_dicts = [comment.model_dump() for comment in comments]
        
        # Cache results
        await self.cache.set(cache_key, comment_dicts)
        
        return comment_dicts
    
    async def get_video_transcript(
        self, 
        video_id: str, 
        language: str = "en",
        languages: List[str] = None, 
        auto_generated: bool = True
    ) -> Dict[str, Any]:
        """
        Get transcript for a video.
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['en'])
            
        Returns:
            List of transcript segments
        """
        if languages is None:
            languages = [language]
        
        cache_key = f"transcript_{video_id}_{'_'.join(languages)}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Try to get transcript using youtube-transcript-api
            # First try manually uploaded transcripts, then auto-generated
            transcript_list = None
            
            # Try getting manually uploaded transcripts first
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                self.logger.debug(f"Found manual transcript for {video_id}")
            except Exception as manual_error:
                self.logger.debug(f"No manual transcript for {video_id}: {manual_error}")
                
                # If manual fails and auto_generated is True, try auto-generated
                if auto_generated:
                    try:
                        # Get available transcripts first to check what's available
                        available = YouTubeTranscriptApi.list_transcripts(video_id)
                        
                        # Try to find auto-generated transcript in preferred languages
                        for lang in languages:
                            try:
                                transcript = available.find_generated_transcript([lang])
                                transcript_list = transcript.fetch()
                                self.logger.debug(f"Found auto-generated transcript for {video_id} in {lang}")
                                break
                            except:
                                continue
                        
                        # If no specific language found, try any auto-generated
                        if not transcript_list:
                            for transcript in available:
                                if transcript.is_generated:
                                    transcript_list = transcript.fetch()
                                    self.logger.debug(f"Found auto-generated transcript for {video_id} in {transcript.language_code}")
                                    break
                                    
                    except Exception as auto_error:
                        self.logger.debug(f"No auto-generated transcript for {video_id}: {auto_error}")
            
            if not transcript_list:
                raise ValueError("No transcripts available for this video")
            
            # Convert to our format
            transcripts = []
            for segment in transcript_list:
                transcript = Transcript(
                    start=segment['start'],
                    end=segment['start'] + segment['duration'],
                    text=segment['text'],
                    duration=segment['duration']
                )
                transcripts.append(transcript)
            
            # Convert to text format for return
            transcript_text = " ".join([t.text for t in transcripts])
            
            result = {
                "video_id": video_id,
                "language": language,
                "auto_generated": True,  # youtube-transcript-api typically gets auto-generated
                "text": transcript_text,
                "segments": [t.model_dump() for t in transcripts]
            }
            
            # Cache results
            await self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            # Provide more specific error information
            error_msg = str(e)
            if "No transcripts available" in error_msg:
                detailed_error = "This video does not have any transcripts (manual or auto-generated) available. This may be because: 1) The creator disabled captions, 2) The video is too new, 3) The video language is not supported for auto-captions, or 4) The video is a live stream or short video."
            elif "TranscriptsDisabled" in error_msg:
                detailed_error = "Transcripts have been disabled for this video by the creator."
            elif "VideoUnavailable" in error_msg:
                detailed_error = "This video is unavailable (may be private, deleted, or region-blocked)."
            else:
                detailed_error = f"Transcript retrieval failed: {error_msg}"
            
            self.logger.info(f"Transcript unavailable for video {video_id}: {detailed_error}")
            return {
                "video_id": video_id,
                "language": language,
                "auto_generated": False,
                "text": "",
                "segments": [],
                "error": detailed_error,
                "available": False
            }
    
    async def get_channel_videos(
        self, 
        channel_id: str, 
        max_results: int = 50,
        order: str = "date"
    ) -> List[SearchResult]:
        """
        Get videos from a specific channel.
        
        Args:
            channel_id: YouTube channel ID or @username
            max_results: Maximum number of videos to retrieve
            order: Sort order (date, relevance, viewCount)
            
        Returns:
            List of videos from the channel
        """
        # Handle @username format by first getting channel ID
        if channel_id.startswith('@'):
            username = self._normalize_username(channel_id)
            # Get channel info to resolve username to channel ID
            channel_info = await self.get_channel_info(channel_usernames=[username])
            if not channel_info:
                raise ValueError(f"Channel not found for username: {channel_id}")
            channel_id = channel_info[0]['id']
        
        cache_key = f"channel_videos_{channel_id}_{max_results}_{order}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return [SearchResult(**item) for item in cached_result]
        
        # Use search API with channel filter
        search_params = {
            'part': 'snippet',
            'channelId': channel_id,
            'maxResults': min(max_results, 50),
            'order': order,
            'type': 'video'
        }
        
        # Make API call
        response = await self._make_api_call('search', **search_params)
        
        # Process results
        results = []
        for item in response.get('items', []):
            snippet = item['snippet']
            result = SearchResult(
                video_id=item['id']['videoId'],
                title=snippet['title'],
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                published_at=snippet['publishedAt'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                description=snippet['description']
            )
            results.append(result)
        
        # Cache results
        await self.cache.set(cache_key, [result.model_dump() for result in results])
        
        return results
    
    async def get_trending_videos(
        self, 
        category_id: Optional[str] = None,
        region_code: str = "US",
        max_results: int = 50
    ) -> List[SearchResult]:
        """
        Get trending videos.
        
        Args:
            category_id: Video category ID (optional)
            region_code: Region code for trending videos
            max_results: Maximum number of videos
            
        Returns:
            List of trending videos
        """
        cache_key = f"trending_{category_id}_{region_code}_{max_results}"
        
        # Check cache (shorter TTL for trending videos)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return [SearchResult(**item) for item in cached_result]
        
        # Use videos endpoint with chart parameter
        params = {
            'part': 'snippet',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': min(max_results, 50)
        }
        
        if category_id:
            params['videoCategoryId'] = category_id
        
        # Make API call
        response = await self._make_api_call('videos', **params)
        
        # Process results
        results = []
        for item in response.get('items', []):
            snippet = item['snippet']
            result = SearchResult(
                video_id=item['id'],
                title=snippet['title'],
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                published_at=snippet['publishedAt'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                description=snippet['description']
            )
            results.append(result)
        
        # Cache with shorter TTL (30 minutes)
        await self.cache.set(cache_key, [result.model_dump() for result in results], ttl=1800)
        
        return results