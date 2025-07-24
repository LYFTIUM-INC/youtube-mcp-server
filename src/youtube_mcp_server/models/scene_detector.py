"""
Scene detection models for video analysis.
Provides scene boundary detection using various computer vision techniques.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Import dependencies with graceful fallbacks
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from scenedetect import detect, ContentDetector, ThresholdDetector
    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SceneChange:
    """Represents a detected scene change."""
    timestamp: float
    confidence: float
    method: str
    description: str
    metadata: Dict[str, Any]

@dataclass
class SceneSegment:
    """Represents a video scene segment."""
    start_time: float
    end_time: float
    duration: float
    scene_id: int
    confidence: float
    characteristics: Dict[str, Any]

class SceneDetector:
    """
    Scene detection using computer vision techniques.
    Supports multiple detection methods including content-based and threshold-based.
    """
    
    def __init__(self, 
                 threshold: float = 0.3,
                 min_scene_length: float = 1.0):
        self.threshold = threshold
        self.min_scene_length = min_scene_length
        
        # Initialize detector if available
        self.detector = None
        if SCENEDETECT_AVAILABLE:
            self.detector = ContentDetector(threshold=threshold)
        
    def detect_scenes(self, video_path: str, 
                     method: str = "content") -> List[SceneSegment]:
        """
        Detect scene boundaries in video.
        
        Args:
            video_path: Path to video file
            method: Detection method ("content", "threshold", "adaptive")
            
        Returns:
            List of detected scene segments
        """
        if not SCENEDETECT_AVAILABLE:
            logger.warning("PySceneDetect not available - scene detection disabled")
            return []
            
        try:
            # Use PySceneDetect for robust scene detection
            scene_list = detect(video_path, self.detector)
            
            segments = []
            for i, (start_time, end_time) in enumerate(scene_list):
                segments.append(SceneSegment(
                    start_time=start_time.get_seconds(),
                    end_time=end_time.get_seconds(),
                    duration=end_time.get_seconds() - start_time.get_seconds(),
                    scene_id=i,
                    confidence=0.8,  # PySceneDetect doesn't provide confidence
                    characteristics={
                        'method': method,
                        'threshold': self.threshold
                    }
                ))
            
            logger.info(f"Detected {len(segments)} scenes using {method} method")
            return segments
            
        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            return []
    
    def detect_scene_changes(self, video_path: str,
                           method: str = "content") -> List[SceneChange]:
        """
        Detect scene change points in video.
        
        Args:
            video_path: Path to video file
            method: Detection method
            
        Returns:
            List of scene change points
        """
        scenes = self.detect_scenes(video_path, method)
        
        changes = []
        for i, scene in enumerate(scenes[1:], 1):  # Skip first scene
            changes.append(SceneChange(
                timestamp=scene.start_time,
                confidence=scene.confidence,
                method=method,
                description=f"Scene transition {i}",
                metadata={
                    'previous_scene_id': i-1,
                    'next_scene_id': i,
                    'duration_before': scenes[i-1].duration,
                    'duration_after': scene.duration
                }
            ))
        
        return changes
    
    def analyze_scene_content(self, video_path: str,
                            scene_segments: List[SceneSegment]) -> List[Dict[str, Any]]:
        """
        Analyze content characteristics of detected scenes.
        
        Args:
            video_path: Path to video file
            scene_segments: List of scene segments to analyze
            
        Returns:
            List of scene analysis results
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available - scene content analysis disabled")
            return []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            analyses = []
            
            for scene in scene_segments:
                # Sample frames from the scene
                start_frame = int(scene.start_time * fps)
                end_frame = int(scene.end_time * fps)
                
                # Sample 5 frames evenly distributed across the scene
                sample_frames = np.linspace(start_frame, end_frame, 5, dtype=int)
                
                brightness_values = []
                motion_values = []
                
                prev_frame = None
                for frame_num in sample_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    
                    if ret:
                        # Calculate brightness
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        brightness = np.mean(gray)
                        brightness_values.append(brightness)
                        
                        # Calculate motion (if we have a previous frame)
                        if prev_frame is not None:
                            diff = cv2.absdiff(prev_frame, gray)
                            motion = np.mean(diff)
                            motion_values.append(motion)
                        
                        prev_frame = gray
                
                # Compile scene analysis
                analysis = {
                    'scene_id': scene.scene_id,
                    'start_time': scene.start_time,
                    'end_time': scene.end_time,
                    'duration': scene.duration,
                    'avg_brightness': np.mean(brightness_values) if brightness_values else 0,
                    'brightness_variance': np.var(brightness_values) if brightness_values else 0,
                    'avg_motion': np.mean(motion_values) if motion_values else 0,
                    'motion_variance': np.var(motion_values) if motion_values else 0,
                    'frame_samples': len(sample_frames)
                }
                
                # Add scene characteristics
                if analysis['avg_brightness'] > 150:
                    analysis['lighting'] = 'bright'
                elif analysis['avg_brightness'] > 75:
                    analysis['lighting'] = 'medium'
                else:
                    analysis['lighting'] = 'dark'
                
                if analysis['avg_motion'] > 20:
                    analysis['activity'] = 'high'
                elif analysis['avg_motion'] > 10:
                    analysis['activity'] = 'medium'
                else:
                    analysis['activity'] = 'low'
                
                analyses.append(analysis)
            
            cap.release()
            logger.info(f"Analyzed content for {len(analyses)} scenes")
            return analyses
            
        except Exception as e:
            logger.error(f"Scene content analysis failed: {e}")
            return []

class HistogramSceneDetector:
    """
    Histogram-based scene detection for when PySceneDetect is not available.
    """
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    def detect_scenes_by_histogram(self, video_path: str) -> List[SceneSegment]:
        """
        Detect scenes using histogram comparison.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of detected scene segments
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available - histogram scene detection disabled")
            return []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample every 30 frames for efficiency
            frame_interval = 30
            
            histograms = []
            frame_times = []
            
            for frame_num in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    # Calculate histogram
                    hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                    hist = cv2.normalize(hist, hist).flatten()
                    histograms.append(hist)
                    frame_times.append(frame_num / fps)
            
            cap.release()
            
            # Find scene boundaries by comparing histograms
            scene_changes = [0]  # Always start with frame 0
            
            for i in range(1, len(histograms)):
                # Calculate histogram correlation
                correlation = cv2.compareHist(histograms[i-1], histograms[i], cv2.HISTCMP_CORREL)
                
                # If correlation is below threshold, it's a scene change
                if correlation < (1 - self.threshold):
                    scene_changes.append(i)
            
            # Add final frame
            scene_changes.append(len(histograms) - 1)
            
            # Create scene segments
            segments = []
            for i in range(len(scene_changes) - 1):
                start_idx = scene_changes[i]
                end_idx = scene_changes[i + 1]
                
                start_time = frame_times[start_idx]
                end_time = frame_times[end_idx]
                
                segments.append(SceneSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    scene_id=i,
                    confidence=0.7,
                    characteristics={
                        'method': 'histogram',
                        'threshold': self.threshold,
                        'frame_interval': frame_interval
                    }
                ))
            
            logger.info(f"Detected {len(segments)} scenes using histogram method")
            return segments
            
        except Exception as e:
            logger.error(f"Histogram scene detection failed: {e}")
            return []