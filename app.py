import os
import cv2
import sys
from flask import Flask, render_template, Response, jsonify, request
from werkzeug.utils import secure_filename
from main import MiniRoadSignLaneSystem
import config

import logging

# Configure logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = str(config.DATA_DIR / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global state
current_system = None
current_video_path = None
latest_metrics = {
    'fps': 0,
    'offset': 0,
    'curvature': 0,
    'signs': []
}

def generate_frames():
    global current_system, current_video_path, latest_metrics
    
    logging.info("Starting generate_frames")
    
    if not current_video_path:
        logging.error("No video path set")
def upload_file():
    global current_system, current_video_path
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify(latest_metrics)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
