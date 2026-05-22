"""
ASAAP - Anti Sexual Abuse Alerting Program
Inference / Prediction Module

Loads the trained CNN model and provides real-time prediction
on audio chunks. Implements the consecutive distress validation
logic to reduce false positives.

Usage:
    from predict import DistressDetector
    
    detector = DistressDetector()
    label, confidence = detector.predict_chunk(audio_chunk)
    is_alert = detector.should_alert()
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
import warnings
warnings.filterwarnings('ignore')

from utils.config import (
    MODEL_SAVE_PATH, SAMPLE_RATE, CONFIDENCE_THRESHOLD,
    CONSECUTIVE_THRESHOLD, CLASS_LABELS
)
from utils.helpers import setup_logger, pad_or_truncate
from feature_extraction import extract_features_for_model

logger = setup_logger("DistressDetector")


class DistressDetector:
    """
    Real-time distress detection engine.
    
    Loads the trained model and performs inference on audio chunks.
    Tracks consecutive distress predictions to reduce false positives.
    
    Attributes:
        model: Loaded Keras CNN model
        distress_count: Number of consecutive distress predictions
        confidence_threshold: Minimum confidence for distress classification
        consecutive_threshold: Number of consecutive detections for alert
        last_confidence: Most recent prediction confidence
        last_label: Most recent prediction label
    """

    def __init__(self, model_path: str = MODEL_SAVE_PATH,
                 confidence_threshold: float = CONFIDENCE_THRESHOLD,
                 consecutive_threshold: int = CONSECUTIVE_THRESHOLD):
        """
        Initialize the detector and load the model.
        
        Args:
            model_path: Path to the saved Keras model
            confidence_threshold: Minimum confidence for distress (0-1)
            consecutive_threshold: Consecutive detections needed for alert
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.consecutive_threshold = consecutive_threshold

        # State tracking
        self.distress_count = 0
        self.last_confidence = 0.0
        self.last_label = "Normal"
        self._alert_triggered = False

        # Load the model
        self.model = None
        self._load_model()

    def _load_model(self):
        """
        Load the trained Keras model from disk.
        Handles missing model gracefully.
        """
        if not os.path.exists(self.model_path):
            logger.warning(f"Model not found at {self.model_path}")
            logger.warning("Train the model first: python train_model.py")
            logger.warning("Using random predictions until model is available")
            self.model = None
            return

        try:
            logger.info(f"Loading model from {self.model_path}...")
            self.model = keras.models.load_model(self.model_path)
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def predict_chunk(self, audio_chunk: np.ndarray) -> tuple:
        """
        Predict whether an audio chunk contains distress sounds.
        Updates internal state for consecutive detection tracking.
        
        Args:
            audio_chunk: Raw audio numpy array (mono, float32)
        
        Returns:
            Tuple of (label_string, confidence_float)
            e.g., ("Distress", 0.92) or ("Normal", 0.15)
        """
        # Ensure audio is the right length
        audio_chunk = pad_or_truncate(audio_chunk)

        # Extract features shaped for model input
        features = extract_features_for_model(audio_chunk, SAMPLE_RATE)

        # Apply normalization if stats exist
        norm_path = os.path.join(os.path.dirname(self.model_path), "norm_stats.npz")
        if os.path.exists(norm_path):
            try:
                stats = np.load(norm_path)
                mean = stats['mean']
                std = stats['std']
                features = (features - mean) / std
            except Exception as e:
                logger.warning(f"Failed to apply normalization: {e}")

        if self.model is not None:
            # Run model inference
            try:
                prediction = self.model.predict(features, verbose=0)
                confidence = float(prediction[0][0])
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                confidence = 0.0
        else:
            # No model loaded — use random predictions for demo
            confidence = float(np.random.uniform(0, 0.5))

        # Determine label based on confidence
        if confidence > self.confidence_threshold:
            label = "Distress"
            self.distress_count += 1
        else:
            label = "Normal"
            self.distress_count = 0  # Reset on normal detection
            self._alert_triggered = False

        # Update state
        self.last_confidence = confidence
        self.last_label = label

        return label, confidence

    def should_alert(self) -> bool:
        """
        Check if an alert should be triggered based on
        consecutive distress detections.
        
        Returns:
            True if distress has been detected for enough
            consecutive chunks to warrant an alert
        """
        if self.distress_count >= self.consecutive_threshold:
            if not self._alert_triggered:
                self._alert_triggered = True
                logger.warning(
                    f"⚠️ ALERT: Distress detected for "
                    f"{self.distress_count} consecutive chunks!"
                )
                return True
        return False

    def reset(self):
        """
        Reset the detection state.
        Called when monitoring is stopped/restarted.
        """
        self.distress_count = 0
        self.last_confidence = 0.0
        self.last_label = "Normal"
        self._alert_triggered = False
        logger.info("Detection state reset")

    def update_threshold(self, confidence_threshold: float):
        """
        Update the confidence threshold dynamically.
        Allows real-time sensitivity adjustment from the GUI.
        
        Args:
            confidence_threshold: New threshold (0.0 to 1.0)
        """
        self.confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        logger.info(f"Confidence threshold updated to {self.confidence_threshold:.2f}")

    def get_status(self) -> dict:
        """
        Get current detector status for GUI display.
        
        Returns:
            Dictionary with current detection state
        """
        return {
            "label": self.last_label,
            "confidence": self.last_confidence,
            "distress_count": self.distress_count,
            "threshold": self.confidence_threshold,
            "consecutive_needed": self.consecutive_threshold,
            "model_loaded": self.model is not None,
            "alert_active": self._alert_triggered
        }
