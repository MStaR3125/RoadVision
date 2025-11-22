# Configuration for Mini Road-Sign Detector & Lane Predictor
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # Go up one level from backend to root
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
OUTPUT_DIR = DATA_DIR / "processed"

# YOLO Model Configuration
SIGN_CONFIDENCE_THRESHOLD = 0.6  # Increased from 0.5 to 60% for more reliable detections
YOLO_MODEL_PATH = str(MODELS_DIR / "yolov8n.pt")
TRAFFIC_SIGN_MODEL_PATH = YOLO_MODEL_PATH

# Confidence Level Thresholds for Color Coding
CONFIDENCE_HIGH = 0.8    # 80%+ - Green
CONFIDENCE_MEDIUM = 0.6  # 60-79% - Yellow

# Class Name Mapping (clearer labels for users)
CLASS_NAME_MAPPING = {
    'train': 'Large Vehicle',
    'truck': 'Truck',
    'car': 'Car',
    'bus': 'Bus',
    'motorcycle': 'Motorcycle',
    'bicycle': 'Bicycle',
    'person': 'Pedestrian'
}

# Data Paths
GTSDB_PATH = DATA_DIR / "traffic_signs" / "GTSDB"
SAMPLE_VIDEOS_PATH = DATA_DIR / "sample_videos"
LANE_SAMPLES_PATH = DATA_DIR / "lane_detection" / "samples"

# Lane Detection Parameters
NWINDOWS = 9
MARGIN = 80
MINPIX = 50
MIN_LANE_POINTS = 100

# Legacy Perspective Transform Points (not used in resolution-agnostic mode)
SRC_BOTTOM_LEFT = [200, 720]
SRC_BOTTOM_RIGHT = [1100, 720]
SRC_TOP_RIGHT = [700, 460]
SRC_TOP_LEFT = [580, 460]

DST_BOTTOM_LEFT = [300, 720]
DST_BOTTOM_RIGHT = [980, 720]
DST_TOP_RIGHT = [980, 0]
DST_TOP_LEFT = [300, 0]

# Kalman Filter Parameters
DT = 0.1  # Time step
PROCESS_NOISE = 1e-4
MEASUREMENT_NOISE = 1e-2
INITIAL_UNCERTAINTY = 1e3

# Alert Thresholds
LANE_OFFSET_THRESHOLD = 0.5  # meters
CURVATURE_ALERT_THRESHOLD = 500

# Video Processing
TARGET_FPS = 30
PROCESSING_SKIP_FRAMES = 1
