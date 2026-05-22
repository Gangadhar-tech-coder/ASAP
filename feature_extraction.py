"""
ASAAP - Anti Sexual Abuse Alerting Program
Feature Extraction Module

Extracts audio features (MFCC or Mel Spectrogram) from raw audio
chunks for both training and real-time inference.

Features are extracted identically during training and inference
to ensure consistent model behavior.
"""

import numpy as np
import librosa

from utils.config import (
    SAMPLE_RATE, N_MFCC, MFCC_MAX_LEN,
    N_MELS, N_FFT, HOP_LENGTH, MEL_MAX_LEN,
    FEATURE_TYPE
)
from utils.helpers import normalize_audio, pad_or_truncate, setup_logger

logger = setup_logger("FeatureExtraction")


def preprocess_audio(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Preprocess raw audio: convert to mono, normalize, and resample.
    
    Args:
        audio: Raw audio array (may be multi-channel)
        sr: Target sample rate
    
    Returns:
        Preprocessed mono audio array
    """
    # Ensure 1D (mono)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Convert to float32 if needed
    audio = audio.astype(np.float32)

    # Normalize amplitude
    audio = normalize_audio(audio)

    return audio


def extract_mfcc(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Extract MFCC features from audio.
    
    MFCCs capture the timbral characteristics of audio,
    which helps distinguish screams/cries from normal speech.
    
    Args:
        audio: Preprocessed audio array
        sr: Sample rate
    
    Returns:
        MFCC feature matrix of shape (N_MFCC, MFCC_MAX_LEN)
    """
    # Extract MFCCs
    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=N_MFCC,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH
    )

    # Pad or truncate time axis to fixed length
    if mfcc.shape[1] < MFCC_MAX_LEN:
        pad_width = MFCC_MAX_LEN - mfcc.shape[1]
        mfcc = np.pad(mfcc, ((0, 0), (0, pad_width)), mode='constant')
    else:
        mfcc = mfcc[:, :MFCC_MAX_LEN]

    return mfcc


def extract_mel_spectrogram(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Extract Mel Spectrogram features from audio.
    
    Mel spectrograms provide a 2D "image" representation of sound,
    ideal for CNN-based classification. They capture both frequency
    content and temporal dynamics.
    
    Args:
        audio: Preprocessed audio array
        sr: Sample rate
    
    Returns:
        Mel spectrogram matrix of shape (N_MELS, MEL_MAX_LEN)
    """
    # Compute mel spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=N_MELS,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH
    )

    # Convert power spectrogram to decibels for better dynamic range
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Pad or truncate time axis to fixed length
    if mel_spec_db.shape[1] < MEL_MAX_LEN:
        pad_width = MEL_MAX_LEN - mel_spec_db.shape[1]
        mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
    else:
        mel_spec_db = mel_spec_db[:, :MEL_MAX_LEN]

    return mel_spec_db


def extract_features(audio: np.ndarray, sr: int = SAMPLE_RATE,
                     feature_type: str = None) -> np.ndarray:
    """
    Extract features based on configured or specified feature type.
    
    This is the main entry point for feature extraction.
    Works identically for training data and real-time chunks.
    
    Args:
        audio: Preprocessed audio array
        sr: Sample rate
        feature_type: Override feature type ("mfcc" or "mel_spectrogram")
    
    Returns:
        Feature matrix with shape suitable for CNN input
    """
    if feature_type is None:
        feature_type = FEATURE_TYPE

    # Preprocess the audio first
    audio = preprocess_audio(audio, sr)

    if feature_type == "mfcc":
        features = extract_mfcc(audio, sr)
    elif feature_type == "mel_spectrogram":
        features = extract_mel_spectrogram(audio, sr)
    else:
        logger.error(f"Unknown feature type: {feature_type}. Using mel_spectrogram.")
        features = extract_mel_spectrogram(audio, sr)

    return features


def extract_features_for_model(audio: np.ndarray, sr: int = SAMPLE_RATE,
                                feature_type: str = None) -> np.ndarray:
    """
    Extract features and reshape for CNN model input.
    Adds batch and channel dimensions.
    
    Args:
        audio: Raw or preprocessed audio array
        sr: Sample rate
        feature_type: Override feature type
    
    Returns:
        Feature array with shape (1, height, width, 1) — ready for model
    """
    features = extract_features(audio, sr, feature_type)

    # Add batch dimension and channel dimension: (1, H, W, 1)
    features = features[np.newaxis, ..., np.newaxis]

    return features


def load_audio_file(filepath: str, sr: int = SAMPLE_RATE):
    """
    Load an audio file and return as numpy array.
    Handles various formats (.wav, .mp3, .ogg, etc.)
    
    Args:
        filepath: Path to audio file
        sr: Target sample rate for resampling
    
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    try:
        audio, file_sr = librosa.load(filepath, sr=sr, mono=True)
        return audio, sr
    except Exception as e:
        logger.error(f"Failed to load audio file {filepath}: {e}")
        return None, None
