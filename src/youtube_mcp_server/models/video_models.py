"""
Video analysis models for scene detection and visual content understanding.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Import dependencies with graceful fallbacks
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    import torchvision.transforms as transforms
    from torchvision import models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

try:
    import scenedetect
    from scenedetect import ContentDetector, AdaptiveDetector
    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SceneChange:
    """Represents a detected scene change."""
    timestamp: float
    confidence: float
    frame_number: int
    change_type: str  # 'cut', 'fade', 'dissolve', 'motion'
    description: str

@dataclass
class ObjectDetection:
    """Represents a detected object in a frame."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    timestamp: float
    frame_number: int

class VideoAnalyzer:
    """
    Comprehensive video analysis using computer vision techniques.
    Provides scene detection, object detection, and visual content analysis.
    """
    
    def __init__(self, 
                 scene_threshold: float = 0.3,
                 use_gpu: bool = True,
                 model_cache_dir: Optional[Path] = None):
        self.scene_threshold = scene_threshold
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        self.model_cache_dir = model_cache_dir or Path("model_cache")
        self.model_cache_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self._init_models()
        
    def _init_models(self):
        """Initialize computer vision models."""
        self.models_loaded = {
            'yolo': False,
            'resnet': False,
            'opencv': CV2_AVAILABLE
        }
        
        try:
            # YOLO for object detection
            if ULTRALYTICS_AVAILABLE:
                try:
                    yolo_path = self.model_cache_dir / "yolov8n.pt"
                    self.yolo_model = YOLO('yolov8n.pt')
                    self.models_loaded['yolo'] = True
                    logger.info(f"Loaded YOLO model on {self.device}")
                except Exception as e:
                    logger.warning(f"Failed to load YOLO model: {e}")
                    self.yolo_model = None
            else:
                logger.warning("Ultralytics not available - object detection disabled")
                self.yolo_model = None
            
            # ResNet for scene classification
            if TORCH_AVAILABLE:
                try:
                    self.scene_model = models.resnet50(pretrained=True)
                    self.scene_model.eval()
                    self.scene_model.to(self.device)
                    self.models_loaded['resnet'] = True
                    
                    # Image preprocessing
                    self.transform = transforms.Compose([
                        transforms.ToPILImage(),
                        transforms.Resize((224, 224)),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                           std=[0.229, 0.224, 0.225])
                    ])
                    logger.info("ResNet scene classification model loaded")
                except Exception as e:
                    logger.warning(f"Failed to load ResNet model: {e}")
                    self.scene_model = None
                    self.transform = None
            else:
                logger.warning("PyTorch not available - deep scene analysis disabled")
                self.scene_model = None
                self.transform = None
            
            if not CV2_AVAILABLE:
                logger.warning("OpenCV not available - basic scene detection disabled")
            
            logger.info(f"Video analysis initialized - Models loaded: {self.models_loaded}")
            
        except Exception as e:
            logger.error(f"Failed to initialize video models: {e}")
            # Don't raise here - allow graceful degradation
    
    def detect_scenes(self, video_path: str, 
                     method: str = "histogram") -> List[SceneChange]:
        """
        Detect scene changes in video using various methods.
        
        Args:
            video_path: Path to video file
            method: Detection method ('histogram', 'optical_flow', 'deep', 'scenedetect')
            
        Returns:
            List of detected scene changes
        """
        # Try PySceneDetect first if available (most robust)
        if method == "scenedetect" and SCENEDETECT_AVAILABLE:
            return self._scenedetect_detection(video_path)
        
        # Fallback to OpenCV-based methods
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available - cannot perform scene detection")
            return []
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        scene_changes = []
        
        try:
            if method == "histogram":
                scene_changes = self._histogram_scene_detection(cap, fps)
            elif method == "optical_flow":
                scene_changes = self._optical_flow_scene_detection(cap, fps)
            elif method == "deep":
                if self.models_loaded['resnet']:
                    scene_changes = self._deep_scene_detection(cap, fps)
                else:
                    logger.warning("Deep learning models not available, falling back to histogram")
                    scene_changes = self._histogram_scene_detection(cap, fps)
            else:
                raise ValueError(f"Unknown scene detection method: {method}")
                
        finally:
            cap.release()
            
        return scene_changes
    
    def _scenedetect_detection(self, video_path: str) -> List[SceneChange]:
        """Scene detection using PySceneDetect library (most robust)."""
        try:
            from scenedetect import detect, ContentDetector
            
            # Detect scenes using content detector
            scene_list = detect(video_path, ContentDetector(threshold=self.scene_threshold * 100))
            
            scene_changes = []
            for i, (start_time, end_time) in enumerate(scene_list):
                # Convert to seconds
                start_seconds = start_time.get_seconds()
                
                scene_changes.append(SceneChange(
                    timestamp=start_seconds,
                    confidence=0.9,  # PySceneDetect is highly reliable
                    frame_number=int(start_seconds * 30),  # Assume 30fps
                    change_type='cut',
                    description=f"PySceneDetect scene boundary #{i+1}"
                ))
            
            logger.info(f"PySceneDetect found {len(scene_changes)} scene changes")
            return scene_changes
            
        except Exception as e:
            logger.error(f"PySceneDetect detection failed: {e}")
            return []
    
    def _histogram_scene_detection(self, cap: cv2.VideoCapture, 
                                 fps: float) -> List[SceneChange]:
        """Scene detection using histogram comparison."""
        scene_changes = []
        prev_hist = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Calculate histogram
            hist = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            
            if prev_hist is not None:
                # Compare histograms
                correlation = cv2.compareHist(hist, prev_hist, cv2.HISTCMP_CORREL)
                
                if correlation < (1 - self.scene_threshold):
                    timestamp = frame_count / fps
                    scene_changes.append(SceneChange(
                        timestamp=timestamp,
                        confidence=1 - correlation,
                        frame_number=frame_count,
                        change_type='cut',
                        description=f"Histogram-based scene change detected"
                    ))
                    
            prev_hist = hist
            frame_count += 1
            
        return scene_changes
    
    def _optical_flow_scene_detection(self, cap: cv2.VideoCapture, 
                                    fps: float) -> List[SceneChange]:
        """Scene detection using optical flow analysis."""
        scene_changes = []
        prev_gray = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Calculate optical flow
                flow = cv2.calcOpticalFlowPyrLK(
                    prev_gray, gray, None, None
                )
                
                # Analyze flow magnitude
                if flow[0] is not None:
                    flow_magnitude = np.mean(np.sqrt(
                        flow[0][:, :, 0]**2 + flow[0][:, :, 1]**2
                    ))
                    
                    if flow_magnitude > self.scene_threshold * 50:
                        timestamp = frame_count / fps
                        scene_changes.append(SceneChange(
                            timestamp=timestamp,
                            confidence=min(flow_magnitude / 100, 1.0),
                            frame_number=frame_count,
                            change_type='motion',
                            description=f"Motion-based scene change detected"
                        ))
                        
            prev_gray = gray
            frame_count += 1
            
        return scene_changes
    
    def _deep_scene_detection(self, cap: cv2.VideoCapture, 
                            fps: float) -> List[SceneChange]:
        """Scene detection using deep learning features."""
        scene_changes = []
        prev_features = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Extract deep features
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_tensor = self.transform(frame_rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                features = self.scene_model(input_tensor)
                features = torch.nn.functional.normalize(features, dim=1)
                
            if prev_features is not None:
                # Calculate cosine similarity
                similarity = torch.cosine_similarity(features, prev_features, dim=1)
                
                if similarity.item() < (1 - self.scene_threshold):
                    timestamp = frame_count / fps
                    scene_changes.append(SceneChange(
                        timestamp=timestamp,
                        confidence=1 - similarity.item(),
                        frame_number=frame_count,
                        change_type='visual_content',
                        description=f"Deep learning-based scene change detected"
                    ))
                    
            prev_features = features
            frame_count += 1
            
        return scene_changes
    
    def detect_objects(self, video_path: str, 
                      target_classes: Optional[List[str]] = None,
                      confidence_threshold: float = 0.5,
                      sample_interval: int = 30) -> List[ObjectDetection]:
        """
        Detect objects in video frames using YOLO.
        
        Args:
            video_path: Path to video file
            target_classes: Specific classes to detect (None for all)
            confidence_threshold: Minimum confidence for detections
            sample_interval: Process every N frames
            
        Returns:
            List of object detections
        """
        if not self.models_loaded['yolo'] or not CV2_AVAILABLE:
            logger.warning("Object detection not available - YOLO or OpenCV missing")
            return []
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        detections = []
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Sample frames
                if frame_count % sample_interval == 0:
                    results = self.yolo_model(frame, verbose=False)
                    
                    for result in results:
                        boxes = result.boxes
                        if boxes is not None:
                            for box in boxes:
                                confidence = float(box.conf[0])
                                if confidence >= confidence_threshold:
                                    class_id = int(box.cls[0])
                                    class_name = self.yolo_model.names[class_id]
                                    
                                    if target_classes is None or class_name in target_classes:
                                        bbox = box.xyxy[0].cpu().numpy().astype(int)
                                        timestamp = frame_count / fps
                                        
                                        detections.append(ObjectDetection(
                                            class_name=class_name,
                                            confidence=confidence,
                                            bbox=tuple(bbox),
                                            timestamp=timestamp,
                                            frame_number=frame_count
                                        ))
                
                frame_count += 1
                
        finally:
            cap.release()
            
        return detections

class SceneDetector:
    """
    Specialized scene detection with advanced algorithms.
    Combines multiple detection methods for robust scene boundary detection.
    """
    
    def __init__(self, video_analyzer: VideoAnalyzer):
        self.video_analyzer = video_analyzer
        
    def detect_scene_boundaries(self, video_path: str, 
                              methods: List[str] = None,
                              consensus_threshold: float = 0.6) -> List[SceneChange]:
        """
        Detect scene boundaries using multiple methods and consensus.
        
        Args:
            video_path: Path to video file
            methods: List of detection methods to use (None for auto-select)
            consensus_threshold: Minimum agreement between methods
            
        Returns:
            Consensus scene changes
        """
        # Auto-select best available methods
        if methods is None:
            if SCENEDETECT_AVAILABLE:
                # PySceneDetect is most reliable - use it alone
                return self.video_analyzer.detect_scenes(video_path, "scenedetect")
            elif CV2_AVAILABLE:
                # Use multiple OpenCV methods for consensus
                methods = ["histogram", "optical_flow"]
                if self.video_analyzer.models_loaded.get('resnet', False):
                    methods.append("deep")
            else:
                logger.error("No scene detection methods available")
                return []
        
        all_detections = {}
        
        # Run each detection method
        for method in methods:
            try:
                detections = self.video_analyzer.detect_scenes(video_path, method)
                all_detections[method] = detections
                logger.info(f"{method} detected {len(detections)} scene changes")
            except Exception as e:
                logger.warning(f"Scene detection method {method} failed: {e}")
                
        # Find consensus
        return self._find_consensus(all_detections, consensus_threshold)
    
    def _find_consensus(self, all_detections: Dict[str, List[SceneChange]], 
                       threshold: float) -> List[SceneChange]:
        """Find consensus scene changes across detection methods."""
        if not all_detections:
            return []
            
        # Collect all timestamps
        all_timestamps = []
        for detections in all_detections.values():
            all_timestamps.extend([d.timestamp for d in detections])
            
        if not all_timestamps:
            return []
            
        # Group nearby timestamps (within 1 second)
        all_timestamps.sort()
        timestamp_groups = []
        current_group = [all_timestamps[0]]
        
        for ts in all_timestamps[1:]:
            if ts - current_group[-1] <= 1.0:
                current_group.append(ts)
            else:
                timestamp_groups.append(current_group)
                current_group = [ts]
        timestamp_groups.append(current_group)
        
        # Find consensus groups
        consensus_scenes = []
        num_methods = len(all_detections)
        
        for group in timestamp_groups:
            if len(group) >= num_methods * threshold:
                avg_timestamp = sum(group) / len(group)
                consensus_scenes.append(SceneChange(
                    timestamp=avg_timestamp,
                    confidence=len(group) / num_methods,
                    frame_number=int(avg_timestamp * 30),  # Assume 30fps
                    change_type='consensus',
                    description=f"Consensus scene change from {len(group)} detections"
                ))
                
        return consensus_scenes