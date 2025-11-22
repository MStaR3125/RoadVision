import cv2
import numpy as np
from . import config

class LaneDetector:
    def __init__(self):
        """Initialize lane detection pipeline"""
        self.M = None
        self.Minv = None
        self.left_fit = None
        self.right_fit = None
        
    def _get_perspective_transform(self, width, height):
        """Calculate perspective transformation matrices dynamically"""
        # Dynamic source points based on image size
        # Trapezoid: Bottom is wide, top is narrow
        src = np.float32([
            [width * 0.15, height],           # Bottom Left
            [width * 0.85, height],           # Bottom Right
            [width * 0.55, height * 0.64],    # Top Right
            [width * 0.45, height * 0.64],    # Top Left
        ])
        
        # Destination points (rectangle)
        dst = np.float32([
            [width * 0.25, height],           # Bottom Left
            [width * 0.75, height],           # Bottom Right
            [width * 0.75, 0],                # Top Right
            [width * 0.25, 0],                # Top Left
        ])
        
        M = cv2.getPerspectiveTransform(src, dst)
        Minv = cv2.getPerspectiveTransform(dst, src)
        return M, Minv
    
    def _color_threshold(self, img):
        """Apply color thresholds for white and yellow lane lines"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Yellow lane detection
        yellow_lower = np.array([15, 80, 160])
        yellow_upper = np.array([40, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        
        # White lane detection  
        white_lower = np.array([0, 0, 200])
        white_upper = np.array([255, 20, 255])
        white_mask = cv2.inRange(hsv, white_lower, white_upper)
        
        # Combine masks
        combined_mask = cv2.bitwise_or(yellow_mask, white_mask)
        return combined_mask
    
    def _sliding_window_search(self, binary_warped):
        """Find lane lines using sliding window method"""
        histogram = np.sum(binary_warped[binary_warped.shape[0]//2:,:], axis=0)
        midpoint = int(histogram.shape[0]//2)
        
        leftx_base = np.argmax(histogram[:midpoint])
        rightx_base = np.argmax(histogram[midpoint:]) + midpoint
        
        window_height = int(binary_warped.shape[0]//config.NWINDOWS)
        nonzero = binary_warped.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        
        leftx_current = leftx_base
        rightx_current = rightx_base
        
        left_lane_inds = []
        right_lane_inds = []
        
        for window in range(config.NWINDOWS):
            win_y_low = binary_warped.shape[0] - (window+1)*window_height
            win_y_high = binary_warped.shape[0] - window*window_height
            
            win_xleft_low = leftx_current - config.MARGIN
            win_xleft_high = leftx_current + config.MARGIN
            win_xright_low = rightx_current - config.MARGIN  
            win_xright_high = rightx_current + config.MARGIN
            
            good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                              (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
            good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                               (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]
            
            left_lane_inds.append(good_left_inds)
            right_lane_inds.append(good_right_inds)
            
            if len(good_left_inds) > config.MINPIX:
                leftx_current = int(np.mean(nonzerox[good_left_inds]))
            if len(good_right_inds) > config.MINPIX:
                rightx_current = int(np.mean(nonzerox[good_right_inds]))
        
        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)
        
        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds] 
        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds]
        
        return leftx, lefty, rightx, righty
    
    def _fit_polynomial(self, leftx, lefty, rightx, righty):
        """Fit second order polynomial to lane points"""
        if len(leftx) < config.MIN_LANE_POINTS or len(rightx) < config.MIN_LANE_POINTS:
            return None, None
            
        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)
        
        return left_fit, right_fit
    
    def detect_lanes(self, frame):
        """Main lane detection pipeline"""
        height, width = frame.shape[:2]
        
        # Calculate transform if not already done or if size changed
        if self.M is None:
             self.M, self.Minv = self._get_perspective_transform(width, height)

        # Apply perspective transform
        warped = cv2.warpPerspective(frame, self.M, 
                                   (width, height))
        
        # Color thresholding
        binary = self._color_threshold(warped)
        
        # Morphological operations to clean up
        kernel = np.ones((3,3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find lane pixels
        leftx, lefty, rightx, righty = self._sliding_window_search(binary)
        
        # Fit polynomials
        left_fit, right_fit = self._fit_polynomial(leftx, lefty, rightx, righty)
        
        if left_fit is not None and right_fit is not None:
            self.left_fit = left_fit
            self.right_fit = right_fit
            return {
                'valid': True,
                'left_fit': left_fit,
                'right_fit': right_fit,
                'binary_warped': binary
            }
        else:
            return {
                'valid': False,
                'binary_warped': binary
            }
    
    def draw_lanes(self, img, left_fit, right_fit):
        """Draw detected lanes on original image"""
        if left_fit is None or right_fit is None:
            return img
            
        # Generate x and y values for plotting
        ploty = np.linspace(0, img.shape[0]-1, img.shape[0])
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
        
        # Create image to draw the lines on
        warp_zero = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
        
        # Recast x and y points into usable format for cv2.fillPoly()
        pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
        pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
        pts = np.hstack((pts_left, pts_right))
        
        # Draw lane area
        cv2.fillPoly(warp_zero, np.int_([pts]), (0, 255, 0))
        
        # Draw lane lines
        pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
        pts_right = np.array([np.transpose(np.vstack([right_fitx, ploty]))])
        cv2.polylines(warp_zero, np.int_([pts_left]), False, (255, 0, 0), thickness=8)
        cv2.polylines(warp_zero, np.int_([pts_right]), False, (255, 0, 0), thickness=8)
        
        # Warp back to original image space
        newwarp = cv2.warpPerspective(warp_zero, self.Minv, (img.shape[1], img.shape[0]))
        
        # Combine with original image
        result = cv2.addWeighted(img, 1, newwarp, 0.3, 0)
        return result