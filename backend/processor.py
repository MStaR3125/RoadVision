import cv2
import time
import logging
from pathlib import Path
from .traffic_sign_detector import TrafficSignDetector
from .lane_detector import LaneDetector
from .lane_predictor import LanePredictor
from .utils import draw_overlay, calculate_metrics
from . import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.traffic_detector = None
        self.lane_detector = None
        self.lane_predictor = None
        self.is_initialized = False

    def initialize(self):
        if not self.is_initialized:
            logger.info("Initializing models...")
            self.traffic_detector = TrafficSignDetector(config.YOLO_MODEL_PATH)
            self.lane_detector = LaneDetector()
            self.lane_predictor = LanePredictor()
            self.is_initialized = True
            logger.info("Models initialized.")

    def process_video(self, input_path: str, output_path: str, progress_callback=None):
        """
        Process a video file and save the result.
        progress_callback: function(progress_float)
        """
        self.initialize()
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {input_path}")

        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup writer
        # Use avc1 (H.264) for better browser compatibility
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        alerts = []
        
        logger.info(f"Starting processing: {input_path} -> {output_path}")
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 1. Traffic Sign Detection
                sign_results = self.traffic_detector.detect(frame)
                annotated_frame = self.traffic_detector.annotate_frame(frame, sign_results)
                
                # 2. Lane Detection
                lane_results = self.lane_detector.detect_lanes(frame)
                
                # 3. Lane Prediction & Smoothing
                results = {'signs': sign_results, 'lane_offset': None, 'curvature': None}
                
                if lane_results['valid']:
                    predicted_lanes = self.lane_predictor.update_and_predict(
                        lane_results['left_fit'], 
                        lane_results['right_fit']
                    )
                    
                    final_frame = self.lane_detector.draw_lanes(
                        annotated_frame, 
                        predicted_lanes['left_fit'], 
                        predicted_lanes['right_fit']
                    )
                    
                    metrics = calculate_metrics(predicted_lanes, (height, width))
                    results['lane_offset'] = metrics['offset']
                    results['curvature'] = metrics['curvature']
                    
                else:
                    final_frame = annotated_frame
                    # Use prediction if available (fail-safe)
                    if self.lane_predictor.initialized:
                        self.lane_predictor.predict()
                        # We could draw predicted lanes here even if detection failed
                
                # Add overlay
                results['fps'] = fps # Use source FPS for static video analysis
                final_frame = draw_overlay(final_frame, results, frame_count)
                
                writer.write(final_frame)
                
                frame_count += 1
                if progress_callback and frame_count % 10 == 0:
                    progress = min(1.0, frame_count / total_frames)
                    progress_callback(progress)
                    
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise e
        finally:
            cap.release()
            writer.release()
            logger.info("Processing complete.")
            
        return True
