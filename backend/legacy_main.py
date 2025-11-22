import cv2
import numpy as np
import time
import argparse
import os
from pathlib import Path

from traffic_sign_detector import TrafficSignDetector
from lane_detector import LaneDetector
from lane_predictor import LanePredictor
from utils import draw_overlay, calculate_metrics, log_alerts
import config

class MiniRoadSignLaneSystem:
    def __init__(self, model_path="yolov8n.pt", debug=False):
        self.debug = debug
        if not os.path.exists(model_path):
             print(f"Warning: Model not found at {model_path}. Traffic sign detection may fail.")
        self.traffic_detector = TrafficSignDetector(model_path)
        self.lane_detector = LaneDetector()
        self.lane_predictor = LanePredictor()
        self.frame_count = 0
        self.alerts = []
        
    def process_frame(self, frame):
        """Process single frame for both traffic signs and lanes"""
        start_time = time.time()
        results = {}
        
        # 1. Traffic Sign Detection
        sign_results = self.traffic_detector.detect(frame)
        annotated_frame = self.traffic_detector.annotate_frame(frame, sign_results)
        
        # 2. Lane Detection
        lane_results = self.lane_detector.detect_lanes(frame)
        
        # 3. Lane Prediction & Smoothing
        if lane_results['valid']:
            predicted_lanes = self.lane_predictor.update_and_predict(
                lane_results['left_fit'], 
                lane_results['right_fit']
            )
            
            # Draw lane overlay
            final_frame = self.lane_detector.draw_lanes(
                annotated_frame, 
                predicted_lanes['left_fit'], 
                predicted_lanes['right_fit']
            )
            
            # Calculate metrics
            metrics = calculate_metrics(predicted_lanes, frame.shape)
            results['lane_offset'] = metrics['offset']
            results['curvature'] = metrics['curvature']
            
            # Check for alerts
            self.check_alerts(metrics)
            
        else:
            final_frame = annotated_frame
            results['lane_offset'] = None
            results['curvature'] = None
        
        # Add performance metrics
        fps = 1.0 / (time.time() - start_time)
        results['fps'] = fps
        results['signs'] = sign_results
        if 'binary_warped' in lane_results:
            results['binary_warped'] = lane_results['binary_warped']
        
        return final_frame, results
    
    def check_alerts(self, metrics):
        """Generate lane departure and other alerts"""
        if abs(metrics['offset']) > config.LANE_DEPARTURE_THRESHOLD:
            alert = f"Lane departure warning: offset {metrics['offset']:.2f}m"
            self.alerts.append(alert)
            
    def process_video(self, input_path, output_path=None):
        """Process entire video file"""
        cap = cv2.VideoCapture(input_path)
        writer = None
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            processed_frame, results = self.process_frame(frame)
            
            # Add overlay information
            processed_frame = draw_overlay(processed_frame, results, self.frame_count)
            
            # Display frame
            cv2.imshow('Road Sign & Lane Detection', processed_frame)
            
            if self.debug and 'binary_warped' in results:
                # Show debug view for lane detection
                cv2.imshow('Lane Detection Debug', results['binary_warped'])
            
            # Write to output file
            if output_path and writer is None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                h, w = processed_frame.shape[:2]
                writer = cv2.VideoWriter(output_path, fourcc, 20.0, (w, h))
            
            if writer:
                writer.write(processed_frame)
            
            # Log metrics
            if self.frame_count % 30 == 0:  # Log every 30 frames
                log_alerts(results, self.frame_count, self.alerts)
            
            self.frame_count += 1
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mini Road Sign & Lane Detection System')
    parser.add_argument('--input', type=str, required=True, help='Input video path')
    parser.add_argument('--output', type=str, help='Output video path')
    parser.add_argument('--model', type=str, default=config.YOLO_MODEL_PATH, help='YOLOv8 model path')
    parser.add_argument('--debug', action='store_true', help='Enable debug visualizations')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input video file not found: {args.input}")
        exit(1)
        
    print(f"Processing video: {args.input}")
    print(f"Using model: {args.model}")
    
    try:
        system = MiniRoadSignLaneSystem(args.model, debug=args.debug)
        system.process_video(args.input, args.output)
    except Exception as e:
        print(f"An error occurred: {e}")