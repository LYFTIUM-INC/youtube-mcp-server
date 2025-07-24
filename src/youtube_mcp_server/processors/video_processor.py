"""
Video processing module for advanced trimming and manipulation operations.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import dependencies with graceful fallbacks
try:
    from moviepy import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # Fallback to older import structure
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TrimOperation:
    """Represents a video trimming operation."""
    start_time: float
    end_time: float
    operation_type: str  # 'extract', 'remove', 'fade_in', 'fade_out'
    description: str
    metadata: Dict[str, Any] = None

@dataclass 
class VideoSegment:
    """Represents a video segment with metadata."""
    file_path: str
    start_time: float
    end_time: float
    duration: float
    resolution: Tuple[int, int]
    fps: float
    has_audio: bool

class VideoProcessor:
    """
    High-performance video processor using MoviePy and FFmpeg.
    Provides advanced trimming, concatenation, and format conversion.
    """
    
    def __init__(self, 
                 temp_dir: Optional[Path] = None,
                 use_gpu: bool = True,
                 max_workers: int = 4):
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "youtube_mcp_video"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.use_gpu = use_gpu and self._check_gpu_support()
        self.max_workers = max_workers
        
        logger.info(f"VideoProcessor initialized with GPU support: {self.use_gpu}")
    
    def _check_gpu_support(self) -> bool:
        """Check if GPU acceleration is available for FFmpeg."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hwaccels'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'cuda' in result.stdout or 'nvenc' in result.stdout
        except Exception:
            return False
    
    def smart_trim(self, 
                   input_path: str,
                   trim_operations: List[TrimOperation],
                   output_path: str,
                   output_format: str = "mp4",
                   quality: str = "high") -> Dict[str, Any]:
        """
        Perform smart trimming operations on video.
        
        Args:
            input_path: Path to input video
            trim_operations: List of trimming operations to perform
            output_path: Path for output video
            output_format: Output video format
            quality: Output quality ('low', 'medium', 'high', 'lossless')
            
        Returns:
            Dictionary with operation results and metadata
        """
        if not MOVIEPY_AVAILABLE:
            return {
                'success': False,
                'error': 'MoviePy not available for video processing',
                'message': 'Please install moviepy: pip install moviepy'
            }
            
        try:
            # Load video
            with VideoFileClip(input_path) as video:
                original_duration = video.duration
                
                # Process trim operations
                segments = []
                for operation in trim_operations:
                    if operation.operation_type == 'extract':
                        segment = video.subclip(operation.start_time, operation.end_time)
                        segments.append(segment)
                    elif operation.operation_type == 'remove':
                        # Split around the removed section
                        if operation.start_time > 0:
                            segments.append(video.subclip(0, operation.start_time))
                        if operation.end_time < original_duration:
                            segments.append(video.subclip(operation.end_time, original_duration))
                
                # Concatenate segments if multiple
                if len(segments) > 1:
                    final_video = concatenate_videoclips(segments)
                elif len(segments) == 1:
                    final_video = segments[0]
                else:
                    raise ValueError("No valid segments to process")
                
                # Apply quality settings
                codec_params = self._get_codec_params(quality, output_format)
                
                # Write output
                final_video.write_videofile(
                    output_path,
                    **codec_params,
                    temp_audiofile=str(self.temp_dir / f"temp_audio_{hash(output_path)}.m4a"),
                    remove_temp=True
                )
                
                # Clean up
                final_video.close()
                for segment in segments:
                    segment.close()
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'original_duration': original_duration,
                    'final_duration': final_video.duration,
                    'operations_applied': len(trim_operations),
                    'compression_ratio': Path(output_path).stat().st_size / Path(input_path).stat().st_size
                }
                
        except Exception as e:
            logger.error(f"Smart trim failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path,
                'output_path': output_path
            }
    
    def extract_segments_by_timestamps(self,
                                     input_path: str,
                                     timestamps: List[Tuple[float, float]],
                                     output_dir: str,
                                     naming_pattern: str = "segment_{index:03d}") -> List[Dict[str, Any]]:
        """
        Extract multiple video segments based on timestamps.
        
        Args:
            input_path: Path to input video
            timestamps: List of (start_time, end_time) tuples
            output_dir: Directory for output segments
            naming_pattern: Pattern for naming output files
            
        Returns:
            List of extraction results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        try:
            with VideoFileClip(input_path) as video:
                input_format = Path(input_path).suffix
                
                for i, (start_time, end_time) in enumerate(timestamps):
                    try:
                        # Generate output filename
                        output_filename = naming_pattern.format(
                            index=i,
                            start=int(start_time),
                            end=int(end_time),
                            duration=int(end_time - start_time)
                        ) + input_format
                        output_path = output_dir / output_filename
                        
                        # Extract segment
                        segment = video.subclip(start_time, end_time)
                        segment.write_videofile(
                            str(output_path),
                            codec='libx264',
                            audio_codec='aac',
                            temp_audiofile=str(self.temp_dir / f"temp_audio_seg_{i}.m4a"),
                            remove_temp=True,
                            verbose=False,
                            logger=None
                        )
                        
                        segment.close()
                        
                        results.append({
                            'success': True,
                            'segment_index': i,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': end_time - start_time,
                            'output_path': str(output_path),
                            'file_size': output_path.stat().st_size
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to extract segment {i}: {e}")
                        results.append({
                            'success': False,
                            'segment_index': i,
                            'start_time': start_time,
                            'end_time': end_time,
                            'error': str(e)
                        })
                        
        except Exception as e:
            logger.error(f"Failed to load input video: {e}")
            return [{'success': False, 'error': f"Failed to load video: {e}"}]
        
        return results
    
    def batch_process_videos(self,
                           video_operations: List[Dict[str, Any]],
                           max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process multiple videos concurrently.
        
        Args:
            video_operations: List of operation specifications
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of processing results
        """
        max_concurrent = max_concurrent or self.max_workers
        results = []
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all operations
            future_to_operation = {
                executor.submit(self._process_single_operation, op): op
                for op in video_operations
            }
            
            # Collect results
            for future in as_completed(future_to_operation):
                operation = future_to_operation[future]
                try:
                    result = future.result()
                    result['operation_spec'] = operation
                    results.append(result)
                except Exception as e:
                    logger.error(f"Operation failed: {e}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'operation_spec': operation
                    })
        
        return results
    
    def _process_single_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single video operation."""
        op_type = operation.get('type')
        
        if op_type == 'smart_trim':
            return self.smart_trim(
                operation['input_path'],
                operation['trim_operations'],
                operation['output_path'],
                operation.get('output_format', 'mp4'),
                operation.get('quality', 'high')
            )
        elif op_type == 'extract_segments':
            return {
                'success': True,
                'segments': self.extract_segments_by_timestamps(
                    operation['input_path'],
                    operation['timestamps'],
                    operation['output_dir'],
                    operation.get('naming_pattern', 'segment_{index:03d}')
                )
            }
        else:
            raise ValueError(f"Unknown operation type: {op_type}")
    
    def optimize_for_streaming(self,
                             input_path: str,
                             output_path: str,
                             target_bitrate: str = "2M",
                             resolution: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Optimize video for streaming with web-compatible settings.
        
        Args:
            input_path: Path to input video
            output_path: Path for optimized output
            target_bitrate: Target bitrate (e.g., "2M", "1500k")
            resolution: Target resolution (width, height)
            
        Returns:
            Optimization results
        """
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-maxrate', target_bitrate,
                '-bufsize', f"{int(target_bitrate.rstrip('Mk')) * 2}{'M' if 'M' in target_bitrate else 'k'}",
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart'  # Optimize for web streaming
            ]
            
            if resolution:
                cmd.extend(['-vf', f'scale={resolution[0]}:{resolution[1]}'])
            
            if self.use_gpu:
                cmd.extend(['-hwaccel', 'cuda'])
            
            cmd.extend(['-y', output_path])  # Overwrite output
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output_path': output_path,
                    'original_size': Path(input_path).stat().st_size,
                    'optimized_size': Path(output_path).stat().st_size,
                    'compression_ratio': Path(output_path).stat().st_size / Path(input_path).stat().st_size
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'command': ' '.join(cmd)
                }
                
        except Exception as e:
            logger.error(f"Streaming optimization failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_codec_params(self, quality: str, output_format: str) -> Dict[str, Any]:
        """Get codec parameters based on quality setting."""
        base_params = {
            'verbose': False,
            'logger': None
        }
        
        if output_format.lower() == 'mp4':
            base_params.update({
                'codec': 'libx264',
                'audio_codec': 'aac'
            })
            
            if quality == 'lossless':
                base_params['ffmpeg_params'] = ['-crf', '0']
            elif quality == 'high':
                base_params['ffmpeg_params'] = ['-crf', '18']
            elif quality == 'medium':
                base_params['ffmpeg_params'] = ['-crf', '23']
            else:  # low
                base_params['ffmpeg_params'] = ['-crf', '28']
                
        elif output_format.lower() == 'webm':
            base_params.update({
                'codec': 'libvpx-vp9',
                'audio_codec': 'libvorbis'
            })
            
        return base_params
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get comprehensive video information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Video metadata and properties
        """
        try:
            with VideoFileClip(video_path) as video:
                info = {
                    'duration': video.duration,
                    'fps': video.fps,
                    'size': video.size,
                    'has_audio': video.audio is not None,
                    'file_size': Path(video_path).stat().st_size
                }
                
                if video.audio:
                    info['audio_duration'] = video.audio.duration
                    
                return info
                
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {'error': str(e)}
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        try:
            for temp_file in self.temp_dir.glob("temp_*"):
                temp_file.unlink()
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")