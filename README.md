# Mini Road-Sign Detector & Lane Predictor

This project is a real-time road sign detector and lane predictor system.

## Features

- **Traffic Sign Detection:** Utilizes YOLOv8 for real-time traffic sign detection.
- **Lane Detection:** Employs OpenCV for lane detection.
- **Lane Prediction:** Uses a Kalman filter for lane prediction and tracking.

## Project Structure

```
mini-road-sign-detector/
├── main.py                 # Main pipeline implementation
├── traffic_sign_detector.py # YOLOv8 traffic sign detection
├── lane_detector.py        # OpenCV lane detection pipeline
├── lane_predictor.py       # Kalman filter for lane tracking
├── utils.py               # Utility functions
├── config.py              # Configuration parameters
├── requirements.txt       # Dependencies
├── models/                # Pre-trained models directory
├── data/                  # Sample videos and test data
├── output/               # Processed videos and logs
└── README.md             # Documentation
```

## Usage

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the system:**

   ```bash
   python main.py --input <input_video_path> --output <output_video_path>
   ```
