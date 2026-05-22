"""
ASAAP - Anti Sexual Abuse Alerting Program
Central Configuration Module

All tunable parameters for audio capture, feature extraction,
model training, and alert thresholds are defined here.
Modify these values to adjust system behavior.
"""

import os

# ============================================================
# PROJECT PATHS
# ============================================================
# Root directory of the project (parent of /utils)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dataset directories
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")
DISTRESS_DIR = os.path.join(DATASET_DIR, "distress")
NORMAL_DIR = os.path.join(DATASET_DIR, "normal")

# Model save directory
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "asaap_model.keras")

# ============================================================
# AUDIO CAPTURE SETTINGS
# ============================================================
SAMPLE_RATE = 22050          # Hz — standard for librosa/audio ML
CHUNK_DURATION = 2.5         # seconds per audio chunk
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)  # total samples per chunk
CHANNELS = 1                 # mono audio

# ============================================================
# FEATURE EXTRACTION SETTINGS
# ============================================================
# Choose feature type: "mfcc" or "mel_spectrogram"
FEATURE_TYPE = "mel_spectrogram"

# MFCC parameters
N_MFCC = 40                  # number of MFCC coefficients
MFCC_MAX_LEN = 109           # time steps after extraction (pad/truncate)

# Mel Spectrogram parameters
N_MELS = 128                 # number of mel frequency bands
N_FFT = 2048                 # FFT window size
HOP_LENGTH = 512             # hop length between frames
MEL_MAX_LEN = 109            # time steps after extraction (pad/truncate)

# ============================================================
# MODEL ARCHITECTURE SETTINGS
# ============================================================
INPUT_SHAPE_MEL = (N_MELS, MEL_MAX_LEN, 1)   # for mel spectrogram
INPUT_SHAPE_MFCC = (N_MFCC, MFCC_MAX_LEN, 1) # for MFCC

# Training hyperparameters
EPOCHS = 30
BATCH_SIZE = 16
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.2
DROPOUT_RATE = 0.3

# ============================================================
# DETECTION / INFERENCE SETTINGS
# ============================================================
CONFIDENCE_THRESHOLD = 0.8   # minimum confidence to count as distress
CONSECUTIVE_THRESHOLD = 2    # consecutive distress chunks to trigger alert

# ============================================================
# ALERT SETTINGS
# ============================================================
ALARM_DURATION = 1.5         # seconds of alarm tone
ALARM_FREQUENCY = 880        # Hz — A5 note, piercing alert tone

# Email alert (simulated by default)
EMAIL_ENABLED = False
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_SENDER = ""
EMAIL_PASSWORD = ""
EMAIL_RECIPIENT = ""

# GPS simulation — base coordinates (Hyderabad, India as default)
GPS_BASE_LAT = 17.3850
GPS_BASE_LON = 78.4867
GPS_RADIUS_KM = 2.0         # random offset radius

# ============================================================
# SYNTHETIC DATASET SETTINGS
# ============================================================
SYNTHETIC_COUNT_PER_CLASS = 100   # number of samples per class
SYNTHETIC_DURATION = 2.5          # seconds per sample

# ============================================================
# GUI SETTINGS
# ============================================================
APP_TITLE = "ASAAP — Anti Sexual Abuse Alerting Program"
APP_WIDTH = 1000
APP_HEIGHT = 700
THEME_MODE = "dark"              # "dark", "light", or "system"
THEME_COLOR = "blue"             # CustomTkinter color theme

# ============================================================
# CLASS LABELS
# ============================================================
CLASS_LABELS = {0: "Normal", 1: "Distress"}
