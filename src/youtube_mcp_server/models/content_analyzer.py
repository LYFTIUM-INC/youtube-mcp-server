"""
Content analysis models for video and image analysis.
Provides object detection, content classification, and visual analysis.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import os

# Import dependencies with graceful fallbacks
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class DetectedObject:
    """Represents a detected object in video/image."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    timestamp: Optional[float] = None
    frame_number: Optional[int] = None

@dataclass
class ContentSegment:
    """Represents a content segment with detected objects."""
    start_time: float
    end_time: float
    duration: float
    objects: List[DetectedObject]
    dominant_objects: List[str]
    scene_type: str
    confidence: float

class ContentAnalyzer:
    """
    Content analysis using YOLO object detection and computer vision.
    Provides object detection, content classification, and visual analysis.
    """
    
    def __init__(self, 
                 model_size: str = "yolov8n",
                 device: str = "auto",
                 confidence_threshold: float = 0.5):
        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        
        # Force CPU usage if environment variables are set
        force_cpu = (
            os.environ.get("FORCE_CPU") == "1" or 
            os.environ.get("TORCH_DEVICE") == "cpu" or
            os.environ.get("CUDA_VISIBLE_DEVICES") == "" or
            device == "cpu"
        )
        
        if force_cpu:
            self.device = "cpu"
        elif device != "auto":
            self.device = device
        else:
            self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        
        # Load YOLO model
        self.yolo_model = None
        self._load_yolo_model()
    
    def _load_yolo_model(self):
        """Load YOLO model for object detection."""
        if not YOLO_AVAILABLE:
            logger.warning("YOLO not available - object detection disabled")
            return
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - object detection disabled")
            return
            
        try:
            logger.info(f"Loading YOLO {self.model_size} model on {self.device}")
            self.yolo_model = YOLO(f"{self.model_size}.pt")
            
            # Force device
            if hasattr(self.yolo_model, 'model') and hasattr(self.yolo_model.model, 'to'):
                self.yolo_model.model.to(self.device)
            
            logger.info(f"Successfully loaded YOLO {self.model_size} model")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None
    
    def detect_objects_in_frame(self, frame: np.ndarray,
                              timestamp: Optional[float] = None,
                              frame_number: Optional[int] = None) -> List[DetectedObject]:
        """
        Detect objects in a single frame.
        
        Args:
            frame: Video frame as numpy array
            timestamp: Frame timestamp in seconds
            frame_number: Frame number
            
        Returns:
            List of detected objects
        """
        if not self.yolo_model:
            return []
        
        try:
            # Run YOLO detection
            results = self.yolo_model(frame, conf=self.confidence_threshold, device=self.device)
            
            detected_objects = []
            
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    
                    for i in range(len(boxes)):
                        # Get bounding box coordinates
                        bbox = boxes.xyxy[i].cpu().numpy()
                        x1, y1, x2, y2 = map(int, bbox)
                        
                        # Get confidence and class
                        confidence = float(boxes.conf[i].cpu().numpy())
                        class_id = int(boxes.cls[i].cpu().numpy())
                        class_name = self.yolo_model.names[class_id]
                        
                        detected_objects.append(DetectedObject(
                            class_name=class_name,
                            confidence=confidence,
                            bbox=(x1, y1, x2, y2),
                            timestamp=timestamp,
                            frame_number=frame_number
                        ))
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def analyze_video_content(self, video_path: str,
                            sample_interval: float = 2.0) -> List[ContentSegment]:
        """
        Analyze video content by detecting objects at regular intervals.
        
        Args:
            video_path: Path to video file
            sample_interval: Interval between samples in seconds
            
        Returns:
            List of content segments with detected objects
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available - video content analysis disabled")
            return []
        
        if not self.yolo_model:
            logger.warning("YOLO model not available - video content analysis disabled")
            return []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # Sample frames at specified intervals
            frame_interval = int(sample_interval * fps)
            
            all_detections = []
            timestamps = []
            
            for frame_num in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    timestamp = frame_num / fps
                    detections = self.detect_objects_in_frame(frame, timestamp, frame_num)
                    all_detections.extend(detections)
                    timestamps.append(timestamp)
            
            cap.release()
            
            # Create content segments based on object consistency
            segments = self._create_content_segments(all_detections, duration, sample_interval)
            
            logger.info(f"Analyzed video content: {len(segments)} segments, {len(all_detections)} total detections")
            return segments
            
        except Exception as e:
            logger.error(f"Video content analysis failed: {e}")
            return []
    
    def _create_content_segments(self, detections: List[DetectedObject],
                               video_duration: float,
                               sample_interval: float) -> List[ContentSegment]:
        """Create content segments based on detected objects."""
        if not detections:
            return []
        
        # Group detections by timestamp windows
        segment_duration = sample_interval * 5  # 5 samples per segment
        num_segments = int(video_duration / segment_duration) + 1
        
        segments = []
        
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, video_duration)
            
            # Find detections in this time window
            segment_detections = [
                d for d in detections 
                if d.timestamp and start_time <= d.timestamp < end_time
            ]
            
            if not segment_detections:
                continue
            
            # Analyze dominant objects
            object_counts = {}
            for detection in segment_detections:
                object_counts[detection.class_name] = object_counts.get(detection.class_name, 0) + 1
            
            # Sort by frequency
            dominant_objects = sorted(object_counts.keys(), 
                                   key=lambda x: object_counts[x], 
                                   reverse=True)[:5]
            
            # Determine scene type
            scene_type = self._classify_scene_type(dominant_objects)
            
            # Calculate average confidence
            avg_confidence = np.mean([d.confidence for d in segment_detections])
            
            segments.append(ContentSegment(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                objects=segment_detections,
                dominant_objects=dominant_objects,
                scene_type=scene_type,
                confidence=avg_confidence
            ))
        
        return segments
    
    def _classify_scene_type(self, dominant_objects: List[str]) -> str:
        """Classify scene type based on dominant objects."""
        # Scene classification rules
        outdoor_objects = {'tree', 'car', 'truck', 'bus', 'bicycle', 'motorcycle', 'stop sign', 'traffic light'}
        indoor_objects = {'chair', 'couch', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'keyboard', 'mouse'}
        people_objects = {'person'}
        animal_objects = {'dog', 'cat', 'bird', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'}
        food_objects = {'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake'}
        
        # Count object categories
        outdoor_count = sum(1 for obj in dominant_objects if obj in outdoor_objects)
        indoor_count = sum(1 for obj in dominant_objects if obj in indoor_objects)
        people_count = sum(1 for obj in dominant_objects if obj in people_objects)
        animal_count = sum(1 for obj in dominant_objects if obj in animal_objects)
        food_count = sum(1 for obj in dominant_objects if obj in food_objects)
        
        # Classify based on dominant category
        if people_count > 0:
            if outdoor_count > indoor_count:
                return "people_outdoor"
            elif indoor_count > 0:
                return "people_indoor"
            else:
                return "people"
        elif animal_count > 0:
            return "animals"
        elif food_count > 0:
            return "food"
        elif outdoor_count > indoor_count:
            return "outdoor"
        elif indoor_count > 0:
            return "indoor"
        else:
            return "general"
    
    def find_objects_in_video(self, video_path: str,
                            target_objects: List[str],
                            confidence_threshold: Optional[float] = None) -> List[Tuple[float, float]]:
        """
        Find specific objects in video and return their time ranges.
        
        Args:
            video_path: Path to video file
            target_objects: List of object names to find
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of (start_time, end_time) tuples where objects are found
        """
        if confidence_threshold is None:
            confidence_threshold = self.confidence_threshold
        
        # Analyze video content
        segments = self.analyze_video_content(video_path)
        
        # Find segments containing target objects
        matching_segments = []
        
        for segment in segments:
            # Check if any target objects are in dominant objects
            found_objects = [obj for obj in target_objects if obj in segment.dominant_objects]
            
            # Also check individual detections for higher confidence
            for detection in segment.objects:
                if (detection.class_name in target_objects and 
                    detection.confidence >= confidence_threshold):
                    found_objects.append(detection.class_name)
            
            if found_objects:
                matching_segments.append((segment.start_time, segment.end_time))
        
        # Merge overlapping segments
        if not matching_segments:
            return []
        
        matching_segments.sort()
        merged = [matching_segments[0]]
        
        for start, end in matching_segments[1:]:
            if start <= merged[-1][1]:  # Overlapping
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        
        return merged
    
    def get_object_statistics(self, video_path: str) -> Dict[str, Any]:
        """
        Get statistics about objects detected in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with object detection statistics
        """
        segments = self.analyze_video_content(video_path)
        
        if not segments:
            return {
                'total_objects': 0,
                'unique_objects': 0,
                'object_counts': {},
                'scene_types': {},
                'avg_confidence': 0.0
            }
        
        # Collect all detections
        all_detections = []
        for segment in segments:
            all_detections.extend(segment.objects)
        
        # Count objects
        object_counts = {}
        for detection in all_detections:
            object_counts[detection.class_name] = object_counts.get(detection.class_name, 0) + 1
        
        # Count scene types
        scene_types = {}
        for segment in segments:
            scene_types[segment.scene_type] = scene_types.get(segment.scene_type, 0) + 1
        
        # Calculate average confidence
        avg_confidence = np.mean([d.confidence for d in all_detections]) if all_detections else 0.0
        
        return {
            'total_objects': len(all_detections),
            'unique_objects': len(object_counts),
            'object_counts': dict(sorted(object_counts.items(), key=lambda x: x[1], reverse=True)),
            'scene_types': scene_types,
            'avg_confidence': float(avg_confidence),
            'segments_analyzed': len(segments)
        }