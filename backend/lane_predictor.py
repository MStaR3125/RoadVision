import numpy as np
from . import config

class LanePredictor:
    def __init__(self):
        """Initialize Kalman filter for lane tracking and prediction"""
        # State: [left_a, left_b, left_c, right_a, right_b, right_c, 
        #         left_a_dot, left_b_dot, left_c_dot, right_a_dot, right_b_dot, right_c_dot]
        self.n_states = 12
        self.n_measurements = 6
        
        # State transition matrix (constant velocity model)
        self.F = np.eye(self.n_states)
        self.F[0:6, 6:12] = np.eye(6) * config.DT  # Position = position + velocity * dt
        
        # Measurement matrix (we observe polynomial coefficients directly)
        self.H = np.zeros((self.n_measurements, self.n_states))
        self.H[0:6, 0:6] = np.eye(6)
        
        # Process noise covariance
        self.Q = np.eye(self.n_states) * config.PROCESS_NOISE
        
        # Measurement noise covariance  
        self.R = np.eye(self.n_measurements) * config.MEASUREMENT_NOISE
        
        # Initial state covariance
        self.P = np.eye(self.n_states) * config.INITIAL_UNCERTAINTY
        
        # Initial state
        self.x = np.zeros(self.n_states)
        
        self.initialized = False
        
    def predict(self):
        """Kalman filter prediction step"""
        if not self.initialized:
            return
            
        # Predict state
        self.x = self.F @ self.x
        
        # Predict covariance  
        self.P = self.F @ self.P @ self.F.T + self.Q
        
    def update(self, left_fit, right_fit):
        """Kalman filter update step"""
        z = np.concatenate([left_fit, right_fit])
        
        if not self.initialized:
            # Initialize state with first measurement
            self.x[0:6] = z
            self.initialized = True
            return
        
        # Innovation
        y = z - self.H @ self.x
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.x = self.x + K @ y
        
        # Update covariance
        I = np.eye(self.n_states)
        self.P = (I - K @ self.H) @ self.P
        
    def update_and_predict(self, left_fit, right_fit):
        """Update with current measurement and predict next state"""
        self.update(left_fit, right_fit)
        self.predict()
        
        # Extract polynomial coefficients
        left_fit_smooth = self.x[0:3]
        right_fit_smooth = self.x[3:6]
        
        return {
            'left_fit': left_fit_smooth,
            'right_fit': right_fit_smooth,
            'confidence': self._calculate_confidence()
        }
        
    def _calculate_confidence(self):
        """Calculate confidence based on covariance trace"""
        if not self.initialized:
            return 0.0
        return min(1.0, 1.0 / (1.0 + np.trace(self.P[0:6, 0:6])))