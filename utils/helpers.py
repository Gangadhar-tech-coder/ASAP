"""
ASAAP - Anti Sexual Abuse Alerting Program
Shared Utility Functions

Provides helper functions for audio normalization, padding,
truncation, directory management, and logging setup.
"""

import os
import logging
import numpy as np
from datetime import datetime

from utils.config import SAMPLE_RATE, CHUNK_SAMPLES


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Create and configure a logger with console output.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)s — %(levelname)s — %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """
    Normalize audio signal to range [-1.0, 1.0].
    Prevents division by zero for silent audio.
    
    Args:
        audio: Raw audio numpy array
    
    Returns:
        Normalized audio array
    """
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        return audio / max_val
    return audio


def pad_or_truncate(audio: np.ndarray, target_length: int = CHUNK_SAMPLES) -> np.ndarray:
    """
    Ensure audio array is exactly `target_length` samples.
    Pads with zeros if too short, truncates if too long.
    
    Args:
        audio: Audio numpy array
        target_length: Desired number of samples
    
    Returns:
        Audio array of exactly target_length
    """
    if len(audio) > target_length:
        # Truncate to target length
        return audio[:target_length]
    elif len(audio) < target_length:
        # Pad with zeros at the end
        padding = target_length - len(audio)
        return np.pad(audio, (0, padding), mode='constant', constant_values=0)
    return audio


def ensure_directories():
    """
    Create all necessary project directories if they don't exist.
    Called at startup to ensure folder structure is ready.
    """
    from utils.config import DATASET_DIR, DISTRESS_DIR, NORMAL_DIR, MODELS_DIR

    dirs = [DATASET_DIR, DISTRESS_DIR, NORMAL_DIR, MODELS_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def get_timestamp() -> str:
    """
    Get current timestamp as a formatted string.
    
    Returns:
        Timestamp string like '2026-05-07 08:30:15'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_short() -> str:
    """
    Get short timestamp for filenames.
    
    Returns:
        Timestamp string like '20260507_083015'
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def calculate_rms(audio: np.ndarray) -> float:
    """
    Calculate Root Mean Square energy of audio signal.
    Useful for detecting silence vs. active audio.
    
    Args:
        audio: Audio numpy array
    
    Returns:
        RMS energy value
    """
    return float(np.sqrt(np.mean(audio ** 2)))


def is_silent(audio: np.ndarray, threshold: float = 0.01) -> bool:
    """
    Check if an audio chunk is essentially silent.
    
    Args:
        audio: Audio numpy array
        threshold: RMS threshold below which audio is considered silent
    
    Returns:
        True if audio is silent
    """
    return calculate_rms(audio) < threshold
