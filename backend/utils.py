import cv2
import numpy as np
from . import config

def calculate_metrics(lane_results, frame_shape):
    """Calculate vehicle offset and lane curvature"""
    left_fit = lane_results['left_fit']
    right_fit = lane_results['right_fit']
    
    # Image dimensions
    h, w = frame_shape[:2]
    
    # Calculate vehicle position (assuming camera is centered)
    vehicle_center = w / 2
    
    # Calculate lane center at bottom of image
    y_eval = h - 1
    left_lane_bottom = left_fit[0]*(y_eval**2) + left_fit[1]*y_eval + left_fit[2]
    right_lane_bottom = right_fit[0]*(y_eval**2) + right_fit[1]*y_eval + right_fit[2]
    lane_center = (left_lane_bottom + right_lane_bottom) / 2
    
    # Calculate offset in pixels, then convert to meters
    offset_pixels = vehicle_center - lane_center
    xm_per_pix = 3.7 / 700  # meters per pixel in x dimension
    offset_meters = offset_pixels * xm_per_pix
    
    # Calculate radius of curvature
    ym_per_pix = 30 / 720  # meters per pixel in y dimension
    
    # Fit new polynomials to x,y in world space
    y_eval_m = y_eval * ym_per_pix
    # Convert polynomial to meters: x = a*y^2 + b*y + c, where y in pixels. For radius, use coefficients in meters.
    # scale y by ym_per_pix and x by xm_per_pix
    a_left_m = left_fit[0] * (xm_per_pix / (ym_per_pix**2))
    b_left_m = left_fit[1] * (xm_per_pix / ym_per_pix)
    a_right_m = right_fit[0] * (xm_per_pix / (ym_per_pix**2))
    b_right_m = right_fit[1] * (xm_per_pix / ym_per_pix)

    left_curverad = ((1 + (2*a_left_m*y_eval_m + b_left_m)**2)**1.5) / np.maximum(1e-6, np.abs(2*a_left_m))
    right_curverad = ((1 + (2*a_right_m*y_eval_m + b_right_m)**2)**1.5) / np.maximum(1e-6, np.abs(2*a_right_m))
    
    # Average the curvatures
    curvature = (left_curverad + right_curverad) / 2
    
    return {
        'offset': offset_meters,
    'curvature': float(curvature),
    'left_curvature': float(left_curverad),
    'right_curvature': float(right_curverad)
    }

def draw_overlay(frame, results, frame_count):
    """Draw performance metrics and alerts on frame"""
    overlay = frame.copy()
    
    # Draw FPS
    fps_text = f"FPS: {results['fps']:.1f}"
    cv2.putText(overlay, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # Draw lane metrics if available
    if results['lane_offset'] is not None:
        offset_text = f"Lane Offset: {results['lane_offset']:.2f}m"
        cv2.putText(overlay, offset_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        curvature_text = f"Curvature: {results['curvature']:.0f}m"
        cv2.putText(overlay, curvature_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Draw detected signs count
    if results['signs']:
        signs_text = f"Signs Detected: {len(results['signs'])}"
        cv2.putText(overlay, signs_text, (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw frame counter
    frame_text = f"Frame: {frame_count}"
    cv2.putText(overlay, frame_text, (frame.shape[1] - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return overlay

def log_alerts(results, frame_count, alerts):
    """Log alerts and metrics to console/file"""
    if alerts:
        print(f"Frame {frame_count}: {', '.join(alerts[-3:])}")  # Show last 3 alerts
    
    if results['lane_offset'] is not None and frame_count % 90 == 0:  # Log every 3 seconds at 30fps
        print(f"Frame {frame_count}: Offset={results['lane_offset']:.2f}m, "
              f"Curvature={results['curvature']:.0f}m, FPS={results['fps']:.1f}")