import cv2
import numpy as np
from ultralytics import YOLO
from . import config

class TrafficSignDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """Initialize YOLOv8 model for traffic sign detection"""
        self.model = YOLO(model_path)
        self.class_names = self.model.names
        
    def detect(self, frame):
        """Detect traffic signs in frame"""
        results = self.model(frame, conf=config.SIGN_CONFIDENCE_THRESHOLD)
        
        detections = []
        for r in results:
            for box in r.boxes:
                # Confidence and class
                conf = float(box.conf[0])
                if conf > config.SIGN_CONFIDENCE_THRESHOLD:
                    # xyxy comes as a tensor of shape [1, 4]
                    x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                    cls = int(box.cls[0])
                    label = self.class_names.get(cls, str(cls)) if isinstance(self.class_names, dict) else self.class_names[cls]
                    
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': conf,
                        'class': label,
                        'class_id': cls
                    })
        
        return detections
    
    def annotate_frame(self, frame, results):
        """Annotate frame with enhanced, color-coded detection labels"""
        annotated = frame.copy()
        
        for detection in results:
            box = detection['bbox']
            x1, y1, x2, y2 = map(int, box)
            class_name = detection['class']
            confidence = detection['confidence']
            
            # Map class name to user-friendly version
            display_name = config.CLASS_NAME_MAPPING.get(class_name, class_name.capitalize())
            
            # Determine confidence level text and color
            if confidence >= config.CONFIDENCE_HIGH:
                color = (0, 255, 0)  # Green
                conf_text = "High Confidence"
            elif confidence >= config.CONFIDENCE_MEDIUM:
                color = (0, 255, 255)  # Yellow
                conf_text = "Medium Confidence"
            else:
                color = (0, 165, 255)  # Orange
                conf_text = "Low Confidence"
            
            # Draw bounding box with thicker lines
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
            
            # Formatted label: "Car [High Confidence]"
            label = f"{display_name} [{conf_text}]"
            
            # Calculate text size for background rectangle
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # Draw background rectangle for text (filled with detection color)
            text_bg_y1 = max(0, y1 - text_height - 12)
            text_bg_y2 = y1
            cv2.rectangle(annotated, (x1, text_bg_y1), (x1 + text_width + 10, text_bg_y2), color, -1)
            
            # Draw white text on colored background
            text_y = max(text_height + 5, y1 - 5)
            cv2.putText(annotated, label, (x1 + 5, text_y), font, font_scale, (255, 255, 255), font_thickness)
        
        return annotated