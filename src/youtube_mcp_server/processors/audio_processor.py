"""
Audio processing module for extraction, manipulation, and format conversion.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
import logging
import tempfile
import subprocess

# Import dependencies with graceful fallbacks
try:
    from pydub import AudioSegment as PydubAudioSegment
    from pydub.silence import split_on_silence, detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class AudioSegment:
    """Represents an audio segment with metadata."""
    file_path: str
    start_time: float
    end_time: float
    duration: float
    sample_rate: int
    channels: int
    format: str

@dataclass
class SilenceSegment:
    """Represents a detected silence segment."""
    start_time: float
    end_time: float
    duration: float
    confidence: float

class AudioProcessor:
    """
    High-performance audio processor using Pydub and librosa.
    Provides audio extraction, trimming, silence removal, and format conversion.
    """
    
    def __init__(self, 
                 temp_dir: Optional[Path] = None,
                 default_sample_rate: int = 22050):
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "youtube_mcp_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.default_sample_rate = default_sample_rate
        
        logger.info("AudioProcessor initialized")
    
    def extract_audio_from_video(self,
                               video_path: str,
                               output_path: str,
                               audio_format: str = "wav",
                               sample_rate: Optional[int] = None,
                               channels: int = 1) -> Dict[str, Any]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to input video
            output_path: Path for extracted audio
            audio_format: Output audio format ('wav', 'mp3', 'flac')
            sample_rate: Target sample rate (None to keep original)
            channels: Number of audio channels (1=mono, 2=stereo)
            
        Returns:
            Extraction results and metadata
        """
        try:
            # Use FFmpeg for high-quality audio extraction
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', self._get_audio_codec(audio_format),
                '-ac', str(channels)  # Audio channels
            ]
            
            if sample_rate:
                cmd.extend(['-ar', str(sample_rate)])
            
            cmd.extend(['-y', output_path])  # Overwrite output
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Get audio info
                audio_info = self.get_audio_info(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'format': audio_format,
                    'extraction_method': 'ffmpeg',
                    **audio_info
                }
            else:
                # Fallback to pydub
                logger.warning(f"FFmpeg extraction failed, trying pydub: {result.stderr}")
                return self._extract_with_pydub(video_path, output_path, audio_format, sample_rate, channels)
                
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_with_pydub(self,
                           video_path: str,
                           output_path: str,
                           audio_format: str,
                           sample_rate: Optional[int],
                           channels: int) -> Dict[str, Any]:
        """Fallback audio extraction using pydub."""
        if not PYDUB_AVAILABLE:
            return {
                'success': False,
                'error': 'Pydub not available for audio extraction',
                'message': 'Please install pydub: pip install pydub'
            }
            
        try:
            audio = PydubAudioSegment.from_file(video_path)
            
            # Apply transformations
            if channels == 1 and audio.channels > 1:
                audio = audio.set_channels(1)
            elif channels == 2 and audio.channels == 1:
                audio = audio.set_channels(2)
                
            if sample_rate and sample_rate != audio.frame_rate:
                audio = audio.set_frame_rate(sample_rate)
            
            # Export audio
            audio.export(output_path, format=audio_format)
            
            return {
                'success': True,
                'output_path': output_path,
                'format': audio_format,
                'extraction_method': 'pydub',
                'duration': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'file_size': Path(output_path).stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Pydub extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trim_audio_by_timestamps(self,
                               input_path: str,
                               timestamps: List[Tuple[float, float]],
                               output_dir: str,
                               output_format: str = "wav",
                               naming_pattern: str = "audio_segment_{index:03d}") -> List[Dict[str, Any]]:
        """
        Trim audio into segments based on timestamps.
        
        Args:
            input_path: Path to input audio
            timestamps: List of (start_time, end_time) tuples in seconds
            output_dir: Directory for output segments
            output_format: Output audio format
            naming_pattern: Pattern for naming output files
            
        Returns:
            List of trimming results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        try:
            audio = PydubAudioSegment.from_file(input_path)
            
            for i, (start_time, end_time) in enumerate(timestamps):
                try:
                    # Convert to milliseconds
                    start_ms = int(start_time * 1000)
                    end_ms = int(end_time * 1000)
                    
                    # Extract segment
                    segment = audio[start_ms:end_ms]
                    
                    # Generate output filename
                    output_filename = naming_pattern.format(
                        index=i,
                        start=int(start_time),
                        end=int(end_time),
                        duration=int(end_time - start_time)
                    ) + f".{output_format}"
                    output_path = output_dir / output_filename
                    
                    # Export segment
                    segment.export(str(output_path), format=output_format)
                    
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
                    logger.error(f"Failed to trim segment {i}: {e}")
                    results.append({
                        'success': False,
                        'segment_index': i,
                        'start_time': start_time,
                        'end_time': end_time,
                        'error': str(e)
                    })
                    
        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            return [{'success': False, 'error': f"Failed to load audio: {e}"}]
        
        return results
    
    def remove_silence(self,
                      input_path: str,
                      output_path: str,
                      silence_threshold: int = -40,
                      min_silence_len: int = 500,
                      keep_silence: int = 100) -> Dict[str, Any]:
        """
        Remove silence from audio file.
        
        Args:
            input_path: Path to input audio
            output_path: Path for output audio
            silence_threshold: Silence threshold in dBFS
            min_silence_len: Minimum silence length in ms to remove
            keep_silence: Amount of silence to keep in ms
            
        Returns:
            Silence removal results
        """
        try:
            audio = PydubAudioSegment.from_file(input_path)
            original_duration = len(audio)
            
            # Split on silence
            audio_segments = split_on_silence(
                audio,
                silence_thresh=silence_threshold,
                min_silence_len=min_silence_len,
                keep_silence=keep_silence
            )
            
            if not audio_segments:
                logger.warning("No audio segments found after silence removal")
                return {
                    'success': False,
                    'error': 'No audio content detected'
                }
            
            # Concatenate segments
            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # Export result
            final_audio.export(output_path, format=Path(output_path).suffix[1:])
            
            final_duration = len(final_audio)
            silence_removed = original_duration - final_duration
            
            return {
                'success': True,
                'output_path': output_path,
                'original_duration': original_duration / 1000.0,
                'final_duration': final_duration / 1000.0,
                'silence_removed': silence_removed / 1000.0,
                'compression_ratio': final_duration / original_duration,
                'segments_count': len(audio_segments)
            }
            
        except Exception as e:
            logger.error(f"Silence removal failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_silence_segments(self,
                              input_path: str,
                              silence_threshold: int = -40,
                              min_silence_len: int = 1000) -> List[SilenceSegment]:
        """
        Detect silence segments in audio.
        
        Args:
            input_path: Path to input audio
            silence_threshold: Silence threshold in dBFS
            min_silence_len: Minimum silence length in ms
            
        Returns:
            List of detected silence segments
        """
        try:
            audio = PydubAudioSegment.from_file(input_path)
            
            # Detect non-silent chunks
            nonsilent_chunks = detect_nonsilent(
                audio,
                silence_thresh=silence_threshold,
                min_silence_len=min_silence_len
            )
            
            # Calculate silence segments
            silence_segments = []
            
            # Silence at the beginning
            if nonsilent_chunks and nonsilent_chunks[0][0] > 0:
                silence_segments.append(SilenceSegment(
                    start_time=0.0,
                    end_time=nonsilent_chunks[0][0] / 1000.0,
                    duration=nonsilent_chunks[0][0] / 1000.0,
                    confidence=1.0
                ))
            
            # Silence between non-silent chunks
            for i in range(len(nonsilent_chunks) - 1):
                silence_start = nonsilent_chunks[i][1] / 1000.0
                silence_end = nonsilent_chunks[i + 1][0] / 1000.0
                
                if silence_end > silence_start:
                    silence_segments.append(SilenceSegment(
                        start_time=silence_start,
                        end_time=silence_end,
                        duration=silence_end - silence_start,
                        confidence=1.0
                    ))
            
            # Silence at the end
            if nonsilent_chunks and nonsilent_chunks[-1][1] < len(audio):
                silence_segments.append(SilenceSegment(
                    start_time=nonsilent_chunks[-1][1] / 1000.0,
                    end_time=len(audio) / 1000.0,
                    duration=(len(audio) - nonsilent_chunks[-1][1]) / 1000.0,
                    confidence=1.0
                ))
            
            return silence_segments
            
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return []
    
    def enhance_audio_quality(self,
                            input_path: str,
                            output_path: str,
                            enhancement_type: str = "denoise") -> Dict[str, Any]:
        """
        Enhance audio quality using various techniques.
        
        Args:
            input_path: Path to input audio
            output_path: Path for enhanced audio
            enhancement_type: Type of enhancement ('denoise', 'normalize', 'compress')
            
        Returns:
            Enhancement results
        """
        try:
            audio = PydubAudioSegment.from_file(input_path)
            enhanced_audio = audio
            
            if enhancement_type == "normalize":
                # Normalize audio to target loudness
                enhanced_audio = enhanced_audio.normalize()
                
            elif enhancement_type == "compress":
                # Dynamic range compression
                enhanced_audio = enhanced_audio.compress_dynamic_range()
                
            elif enhancement_type == "denoise":
                # Basic noise reduction using high-pass filter
                enhanced_audio = enhanced_audio.high_pass_filter(80)
                
            # Export enhanced audio
            enhanced_audio.export(output_path, format=Path(output_path).suffix[1:])
            
            return {
                'success': True,
                'output_path': output_path,
                'enhancement_type': enhancement_type,
                'original_size': Path(input_path).stat().st_size,
                'enhanced_size': Path(output_path).stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def convert_format(self,
                      input_path: str,
                      output_path: str,
                      target_format: str,
                      quality: str = "high") -> Dict[str, Any]:
        """
        Convert audio to different format.
        
        Args:
            input_path: Path to input audio
            output_path: Path for converted audio
            target_format: Target format ('mp3', 'wav', 'flac', 'ogg')
            quality: Conversion quality ('low', 'medium', 'high')
            
        Returns:
            Conversion results
        """
        try:
            audio = PydubAudioSegment.from_file(input_path)
            
            # Set quality parameters
            export_params = {}
            if target_format == "mp3":
                if quality == "high":
                    export_params['bitrate'] = "320k"
                elif quality == "medium":
                    export_params['bitrate'] = "192k"
                else:  # low
                    export_params['bitrate'] = "128k"
            
            # Export in target format
            audio.export(output_path, format=target_format, **export_params)
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'target_format': target_format,
                'quality': quality,
                'original_size': Path(input_path).stat().st_size,
                'converted_size': Path(output_path).stat().st_size,
                'compression_ratio': Path(output_path).stat().st_size / Path(input_path).stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_audio_features(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract audio features using librosa.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary of audio features
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(audio_path, sr=self.default_sample_rate)
            
            # Extract features
            features = {
                'duration': len(y) / sr,
                'sample_rate': sr,
                'rms_energy': float(np.mean(librosa.feature.rms(y=y))),
                'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
                'spectral_rolloff': float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))),
                'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y))),
                'tempo': float(librosa.beat.tempo(y=y, sr=sr)[0])
            }
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfccs, axis=1).tolist()
            features['mfcc_std'] = np.std(mfccs, axis=1).tolist()
            
            return features
            
        except Exception as e:
            logger.error(f"Audio feature extraction failed: {e}")
            return {'error': str(e)}
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get comprehensive audio file information.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio metadata and properties
        """
        try:
            audio = PydubAudioSegment.from_file(audio_path)
            
            return {
                'duration': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'file_size': Path(audio_path).stat().st_size,
                'format': Path(audio_path).suffix[1:].lower(),
                'max_dBFS': audio.max_dBFS,
                'dBFS': audio.dBFS
            }
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {'error': str(e)}
    
    def _get_audio_codec(self, format: str) -> str:
        """Get appropriate audio codec for format."""
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'flac': 'flac',
            'ogg': 'libvorbis',
            'aac': 'aac'
        }
        return codec_map.get(format.lower(), 'pcm_s16le')
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files."""
        try:
            for temp_file in self.temp_dir.glob("temp_audio_*"):
                temp_file.unlink()
            logger.info("Temporary audio files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up temp audio files: {e}")