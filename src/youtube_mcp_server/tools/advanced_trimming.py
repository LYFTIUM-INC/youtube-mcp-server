"""
Advanced video and audio trimming tools with AI-powered scene detection and audio pattern recognition.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import tempfile
import logging
from dataclasses import asdict
import json

# Dependency availability tracking
DEPENDENCIES_STATUS = {
    'moviepy': False,
    'opencv': False,
    'torch': False,
    'whisper': False,
    'ultralytics': False,
    'scenedetect': False,
    'pydub': False,
    'librosa': False
}

def check_dependencies() -> Dict[str, bool]:
    """Check which advanced trimming dependencies are available."""
    global DEPENDENCIES_STATUS
    
    # Check MoviePy
    try:
        import moviepy
        DEPENDENCIES_STATUS['moviepy'] = True
    except ImportError:
        pass
    
    # Check OpenCV
    try:
        import cv2
        DEPENDENCIES_STATUS['opencv'] = True
    except ImportError:
        pass
    
    # Check PyTorch
    try:
        import torch
        DEPENDENCIES_STATUS['torch'] = True
    except ImportError:
        pass
    
    # Check Whisper
    try:
        import whisper
        DEPENDENCIES_STATUS['whisper'] = True
    except ImportError:
        pass
    
    # Check YOLO (Ultralytics)
    try:
        import ultralytics
        DEPENDENCIES_STATUS['ultralytics'] = True
    except ImportError:
        pass
    
    # Check PySceneDetect
    try:
        import scenedetect
        DEPENDENCIES_STATUS['scenedetect'] = True
    except ImportError:
        pass
    
    # Check Pydub
    try:
        import pydub
        DEPENDENCIES_STATUS['pydub'] = True
    except ImportError:
        pass
    
    # Check librosa
    try:
        import librosa
        DEPENDENCIES_STATUS['librosa'] = True
    except ImportError:
        pass
    
    return DEPENDENCIES_STATUS.copy()

def get_missing_dependencies() -> List[str]:
    """Get list of missing dependencies."""
    missing = []
    for dep, available in DEPENDENCIES_STATUS.items():
        if not available:
            missing.append(dep)
    return missing

# Check dependencies on import
check_dependencies()

from ..models.video_models import VideoAnalyzer, SceneDetector, SceneChange, ObjectDetection
from ..models.audio_models import AudioAnalyzer, WhisperTranscriber, SoundClassifier, AudioEvent
from ..processors.video_processor import VideoProcessor, TrimOperation
from ..processors.audio_processor import AudioProcessor
from ..tools.video_downloader import VideoDownloader
from ..infrastructure.cache_manager import CacheManager
from ..infrastructure.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class AdvancedTrimmingOrchestrator:
    """
    Orchestrates advanced video/audio trimming operations with AI-powered analysis.
    Combines computer vision, audio analysis, and intelligent trimming.
    """
    
    def __init__(self, 
                 cache_manager: CacheManager,
                 error_handler: ErrorHandler,
                 temp_dir: Optional[Path] = None,
                 use_gpu: bool = True):
        self.cache_manager = cache_manager
        self.error_handler = error_handler
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "advanced_trimming"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.video_analyzer = VideoAnalyzer(use_gpu=use_gpu, model_cache_dir=self.temp_dir / "models")
        self.scene_detector = SceneDetector(self.video_analyzer)
        self.audio_analyzer = AudioAnalyzer(device="cuda" if use_gpu else "cpu", model_cache_dir=self.temp_dir / "models")
        self.video_processor = VideoProcessor(temp_dir=self.temp_dir, use_gpu=use_gpu)
        self.audio_processor = AudioProcessor(temp_dir=self.temp_dir)
        self.video_downloader = VideoDownloader(
            cache_manager=cache_manager,
            download_dir=str(self.temp_dir)
        )
        
        logger.info("AdvancedTrimmingOrchestrator initialized")
    
    async def smart_trim_video(self,
                             video_url: str,
                             trim_instructions: str,
                             output_format: str = "mp4",
                             quality: str = "high",
                             include_audio: bool = True) -> Dict[str, Any]:
        """
        Perform intelligent video trimming based on natural language instructions.
        
        Args:
            video_url: YouTube video URL
            trim_instructions: Natural language trimming instructions
            output_format: Output video format
            quality: Output quality setting
            include_audio: Whether to include audio in output
            
        Returns:
            Trimming results with metadata
        """
        try:
            # Parse trimming instructions
            trim_spec = await self._parse_trim_instructions(trim_instructions)
            
            # Download video
            from ..tools.video_downloader import DownloadOptions, DownloadQuality
            download_options = DownloadOptions(
                quality=DownloadQuality.MEDIUM,
                extract_audio=include_audio
            )
            download_result = await self.video_downloader.download_video(video_url, download_options)
            if not download_result.success:
                return self.error_handler.handle_error(
                    Exception(f"Video download failed: {download_result.error_message}")
                )
            
            video_path = download_result.file_path
            
            # Determine trimming approach based on instructions
            if trim_spec['type'] == 'time_based':
                return await self._time_based_trim(video_path, trim_spec, output_format, quality)
            elif trim_spec['type'] == 'scene_based':
                return await self._scene_based_trim(video_path, trim_spec, output_format, quality)
            elif trim_spec['type'] == 'audio_pattern':
                return await self._audio_pattern_trim(video_path, trim_spec, output_format, quality)
            elif trim_spec['type'] == 'content_aware':
                return await self._content_aware_trim(video_path, trim_spec, output_format, quality)
            else:
                raise ValueError(f"Unknown trim type: {trim_spec['type']}")
                
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    async def detect_video_scenes(self,
                                video_url: str,
                                detection_method: str = "combined",
                                scene_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Detect scenes in video using various computer vision techniques.
        
        Args:
            video_url: YouTube video URL
            detection_method: Method to use ('histogram', 'optical_flow', 'deep', 'combined')
            scene_threshold: Sensitivity threshold for scene detection
            
        Returns:
            Detected scenes with timestamps and metadata
        """
        try:
            # Download video
            from ..tools.video_downloader import DownloadOptions, DownloadQuality
            download_options = DownloadOptions(quality=DownloadQuality.MEDIUM)
            download_result = await self.video_downloader.download_video(video_url, download_options)
            
            # Handle dict response from video downloader
            if isinstance(download_result, dict):
                success = download_result.get('success', False)
                error_message = download_result.get('error_message', 'Unknown download error')
                file_path = download_result.get('file_path')
            else:
                # Handle DownloadResult object
                success = download_result.success
                error_message = download_result.error_message
                file_path = download_result.file_path
            
            if not success:
                return self.error_handler.handle_error(
                    Exception(f"Video download failed: {error_message}")
                )
            
            video_path = file_path
            
            # Detect scenes
            if detection_method == "combined":
                scene_changes = self.scene_detector.detect_scene_boundaries(
                    video_path,
                    methods=['histogram', 'optical_flow', 'deep'],
                    consensus_threshold=0.6
                )
            else:
                scene_changes = self.video_analyzer.detect_scenes(video_path, detection_method)
            
            # Format results
            scenes = []
            for scene in scene_changes:
                scenes.append({
                    'timestamp': scene.timestamp,
                    'confidence': scene.confidence,
                    'frame_number': scene.frame_number,
                    'change_type': scene.change_type,
                    'description': scene.description
                })
            
            return {
                'success': True,
                'video_url': video_url,
                'detection_method': detection_method,
                'scene_threshold': scene_threshold,
                'scenes_detected': len(scenes),
                'scenes': scenes,
                'video_duration': self.video_processor.get_video_info(video_path).get('duration', 0)
            }
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    async def analyze_audio_patterns(self,
                                   video_url: str,
                                   target_patterns: Optional[List[str]] = None,
                                   include_transcription: bool = True) -> Dict[str, Any]:
        """
        Analyze audio patterns and events in video.
        
        Args:
            video_url: YouTube video URL
            target_patterns: Specific audio patterns to detect
            include_transcription: Whether to include speech transcription
            
        Returns:
            Audio analysis results with detected patterns and events
        """
        try:
            # Download video
            from ..tools.video_downloader import DownloadOptions, DownloadQuality
            download_options = DownloadOptions(quality=DownloadQuality.MEDIUM)
            download_result = await self.video_downloader.download_video(video_url, download_options)
            
            # Handle dict response from video downloader
            if isinstance(download_result, dict):
                success = download_result.get('success', False)
                error_message = download_result.get('error_message', 'Unknown download error')
                file_path = download_result.get('file_path')
            else:
                # Handle DownloadResult object
                success = download_result.success
                error_message = download_result.error_message
                file_path = download_result.file_path
            
            if not success:
                return self.error_handler.handle_error(
                    Exception(f"Video download failed: {error_message}")
                )
            
            video_path = file_path
            
            # Extract audio
            audio_path = str(self.temp_dir / f"audio_{hash(video_url)}.wav")
            audio_extraction = self.audio_processor.extract_audio_from_video(
                video_path, audio_path
            )
            
            if not audio_extraction.get('success'):
                raise Exception(f"Audio extraction failed: {audio_extraction.get('error')}")
            
            # Analyze audio comprehensively
            analysis_result = self.audio_analyzer.analyze_audio(
                audio_path,
                include_transcription=include_transcription,
                include_classification=True,
                target_sounds=target_patterns
            )
            
            return {
                'success': True,
                'video_url': video_url,
                'audio_analysis': analysis_result,
                'target_patterns': target_patterns or [],
                'patterns_found': len(analysis_result.get('sound_patterns', [])),
                'events_detected': len(analysis_result.get('audio_events', [])),
                'speech_segments': len(analysis_result.get('speech_segments', []))
            }
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    async def extract_content_segments(self,
                                     video_url: str,
                                     segment_criteria: Dict[str, Any],
                                     output_dir: str,
                                     context_window: float = 2.0) -> Dict[str, Any]:
        """
        Extract video segments based on specific content criteria.
        
        Args:
            video_url: YouTube video URL
            segment_criteria: Criteria for segment extraction
            output_dir: Directory for output segments
            context_window: Seconds to include before/after detected content
            
        Returns:
            Extraction results with segment information
        """
        try:
            # Download video
            from ..tools.video_downloader import DownloadOptions, DownloadQuality
            download_options = DownloadOptions(quality=DownloadQuality.MEDIUM)
            download_result = await self.video_downloader.download_video(video_url, download_options)
            
            # Handle dict response from video downloader
            if isinstance(download_result, dict):
                success = download_result.get('success', False)
                error_message = download_result.get('error_message', 'Unknown download error')
                file_path = download_result.get('file_path')
            else:
                # Handle DownloadResult object
                success = download_result.success
                error_message = download_result.error_message
                file_path = download_result.file_path
            
            if not success:
                return self.error_handler.handle_error(
                    Exception(f"Video download failed: {error_message}")
                )
            
            video_path = file_path
            
            # Find matching timestamps based on criteria
            timestamps = await self._find_content_timestamps(video_path, segment_criteria, context_window)
            
            if not timestamps:
                return {
                    'success': True,
                    'message': 'No matching content found',
                    'segments_extracted': 0,
                    'criteria': segment_criteria
                }
            
            # Extract video segments
            video_results = self.video_processor.extract_segments_by_timestamps(
                video_path, timestamps, output_dir
            )
            
            # Extract audio segments if requested
            audio_results = []
            if segment_criteria.get('extract_audio', False):
                audio_path = str(self.temp_dir / f"audio_{hash(video_url)}.wav")
                audio_extraction = self.audio_processor.extract_audio_from_video(
                    video_path, audio_path
                )
                
                if audio_extraction.get('success'):
                    audio_results = self.audio_processor.trim_audio_by_timestamps(
                        audio_path, timestamps, output_dir, output_format="wav"
                    )
            
            return {
                'success': True,
                'video_url': video_url,
                'criteria': segment_criteria,
                'timestamps_found': timestamps,
                'segments_extracted': len([r for r in video_results if r.get('success')]),
                'video_segments': video_results,
                'audio_segments': audio_results,
                'output_directory': output_dir
            }
            
        except Exception as e:
            return self.error_handler.handle_error(e)
    
    async def _parse_trim_instructions(self, instructions: str) -> Dict[str, Any]:
        """Parse natural language trimming instructions into structured format."""
        instructions_lower = instructions.lower()
        
        # Time-based patterns
        time_patterns = [
            ('first', 'start'),
            ('last', 'end'),
            ('beginning', 'start'),
            ('end', 'end'),
            ('middle', 'middle')
        ]
        
        # Check for time-based instructions
        for pattern, position in time_patterns:
            if pattern in instructions_lower:
                # Extract duration if specified
                import re
                duration_match = re.search(r'(\d+)\s*(second|minute|hour)s?', instructions_lower)
                if duration_match:
                    duration = float(duration_match.group(1))
                    unit = duration_match.group(2)
                    
                    if unit.startswith('minute'):
                        duration *= 60
                    elif unit.startswith('hour'):
                        duration *= 3600
                    
                    return {
                        'type': 'time_based',
                        'position': position,
                        'duration': duration,
                        'original_instructions': instructions
                    }
        
        # Scene-based patterns
        scene_keywords = ['scene', 'shot', 'cut', 'transition', 'visual']
        if any(keyword in instructions_lower for keyword in scene_keywords):
            return {
                'type': 'scene_based',
                'description': instructions,
                'original_instructions': instructions
            }
        
        # Audio pattern keywords
        audio_keywords = ['sound', 'audio', 'voice', 'music', 'speech', 'bird', 'applause', 'laugh']
        if any(keyword in instructions_lower for keyword in audio_keywords):
            return {
                'type': 'audio_pattern',
                'pattern_description': instructions,
                'original_instructions': instructions
            }
        
        # Default to content-aware
        return {
            'type': 'content_aware',
            'description': instructions,
            'original_instructions': instructions
        }
    
    async def _time_based_trim(self, video_path: str, trim_spec: Dict[str, Any], 
                             output_format: str, quality: str) -> Dict[str, Any]:
        """Perform time-based trimming."""
        video_info = self.video_processor.get_video_info(video_path)
        duration = video_info.get('duration', 0)
        
        position = trim_spec.get('position')
        trim_duration = trim_spec.get('duration', 10)  # Default 10 seconds
        
        if position == 'start':
            start_time = 0
            end_time = min(trim_duration, duration)
        elif position == 'end':
            start_time = max(0, duration - trim_duration)
            end_time = duration
        elif position == 'middle':
            middle = duration / 2
            start_time = max(0, middle - trim_duration / 2)
            end_time = min(duration, middle + trim_duration / 2)
        else:
            raise ValueError(f"Unknown position: {position}")
        
        # Create trim operation
        trim_op = TrimOperation(
            start_time=start_time,
            end_time=end_time,
            operation_type='extract',
            description=f"Time-based trim: {position} {trim_duration}s"
        )
        
        output_path = str(self.temp_dir / f"trimmed_{hash(video_path)}.{output_format}")
        result = self.video_processor.smart_trim(
            video_path, [trim_op], output_path, output_format, quality
        )
        
        return {
            **result,
            'trim_type': 'time_based',
            'trim_specification': trim_spec,
            'extracted_segment': {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time
            }
        }
    
    async def _scene_based_trim(self, video_path: str, trim_spec: Dict[str, Any],
                              output_format: str, quality: str) -> Dict[str, Any]:
        """Perform scene-based trimming using computer vision."""
        # Detect scenes
        scene_changes = self.scene_detector.detect_scene_boundaries(video_path)
        
        if not scene_changes:
            return {
                'success': False,
                'error': 'No scene changes detected',
                'trim_type': 'scene_based'
            }
        
        # For now, extract the first scene as an example
        # In a full implementation, you'd analyze the description to find the best matching scene
        first_scene = scene_changes[0]
        second_scene = scene_changes[1] if len(scene_changes) > 1 else None
        
        start_time = 0
        end_time = first_scene.timestamp if first_scene else 30  # Default to 30s if no scenes
        
        if second_scene:
            end_time = second_scene.timestamp
        
        trim_op = TrimOperation(
            start_time=start_time,
            end_time=end_time,
            operation_type='extract',
            description=f"Scene-based trim: First scene"
        )
        
        output_path = str(self.temp_dir / f"scene_trimmed_{hash(video_path)}.{output_format}")
        result = self.video_processor.smart_trim(
            video_path, [trim_op], output_path, output_format, quality
        )
        
        return {
            **result,
            'trim_type': 'scene_based',
            'scenes_detected': len(scene_changes),
            'selected_scene': {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time
            }
        }
    
    async def _audio_pattern_trim(self, video_path: str, trim_spec: Dict[str, Any],
                                output_format: str, quality: str) -> Dict[str, Any]:
        """Perform audio pattern-based trimming."""
        # Extract audio for analysis
        audio_path = str(self.temp_dir / f"audio_analysis_{hash(video_path)}.wav")
        audio_extraction = self.audio_processor.extract_audio_from_video(
            video_path, audio_path
        )
        
        if not audio_extraction.get('success'):
            return {
                'success': False,
                'error': 'Audio extraction failed',
                'trim_type': 'audio_pattern'
            }
        
        # Find audio patterns
        pattern_description = trim_spec.get('pattern_description', '')
        timestamps = self.audio_analyzer.find_audio_pattern(
            audio_path, pattern_description, context_window=2.0
        )
        
        if not timestamps:
            return {
                'success': False,
                'error': f'No audio patterns found matching: {pattern_description}',
                'trim_type': 'audio_pattern'
            }
        
        # Use the first matching pattern
        start_time, end_time = timestamps[0]
        
        trim_op = TrimOperation(
            start_time=start_time,
            end_time=end_time,
            operation_type='extract',
            description=f"Audio pattern trim: {pattern_description}"
        )
        
        output_path = str(self.temp_dir / f"audio_pattern_trimmed_{hash(video_path)}.{output_format}")
        result = self.video_processor.smart_trim(
            video_path, [trim_op], output_path, output_format, quality
        )
        
        return {
            **result,
            'trim_type': 'audio_pattern',
            'pattern_description': pattern_description,
            'patterns_found': len(timestamps),
            'selected_pattern': {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time
            }
        }
    
    async def _content_aware_trim(self, video_path: str, trim_spec: Dict[str, Any],
                                output_format: str, quality: str) -> Dict[str, Any]:
        """Perform content-aware trimming using combined analysis."""
        # This would implement more sophisticated content analysis
        # For now, fall back to scene-based trimming
        return await self._scene_based_trim(video_path, trim_spec, output_format, quality)
    
    async def _find_content_timestamps(self, video_path: str, criteria: Dict[str, Any],
                                     context_window: float) -> List[Tuple[float, float]]:
        """Find timestamps matching content criteria."""
        timestamps = []
        
        # Audio-based criteria
        if 'audio_pattern' in criteria:
            audio_path = str(self.temp_dir / f"content_audio_{hash(video_path)}.wav")
            audio_extraction = self.audio_processor.extract_audio_from_video(
                video_path, audio_path
            )
            
            if audio_extraction.get('success'):
                audio_timestamps = self.audio_analyzer.find_audio_pattern(
                    audio_path, criteria['audio_pattern'], context_window
                )
                timestamps.extend(audio_timestamps)
        
        # Object detection criteria
        if 'objects' in criteria:
            detections = self.video_analyzer.detect_objects(
                video_path, 
                target_classes=criteria['objects'],
                confidence_threshold=criteria.get('confidence_threshold', 0.5)
            )
            
            # Group detections into time segments
            if detections:
                current_start = detections[0].timestamp
                current_end = detections[0].timestamp
                
                for detection in detections[1:]:
                    if detection.timestamp - current_end <= 2.0:  # Within 2 seconds
                        current_end = detection.timestamp
                    else:
                        timestamps.append((
                            max(0, current_start - context_window),
                            current_end + context_window
                        ))
                        current_start = detection.timestamp
                        current_end = detection.timestamp
                
                # Add the last segment
                timestamps.append((
                    max(0, current_start - context_window),
                    current_end + context_window
                ))
        
        return timestamps
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            self.video_processor.cleanup_temp_files()
            self.audio_processor.cleanup_temp_files()
            logger.info("Advanced trimming cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")