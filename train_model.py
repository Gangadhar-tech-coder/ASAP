"""
ASAAP - Anti Sexual Abuse Alerting Program
Model Training Pipeline

Supports training from:
  1. UrbanSound8K dataset  (dataset/urban/)
  2. Custom distress/normal directories (dataset/distress/, dataset/normal/)

UrbanSound8K class mapping for distress detection:
  DISTRESS (label=1): gun_shot (6), siren (8), car_horn (1)
  NORMAL   (label=0): air_conditioner (0), children_playing (2),
                       dog_bark (3), drilling (4), engine_idling (5),
                       jackhammer (7), street_music (9)

Usage:
    python train_model.py              # auto-detects dataset
    python train_model.py --urban      # force UrbanSound8K
    python train_model.py --custom     # force custom dirs

The trained model is saved to models/asaap_model.keras
"""

import os
import sys
import csv
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

from utils.config import (
    DISTRESS_DIR, NORMAL_DIR, MODEL_SAVE_PATH, MODELS_DIR,
    DATASET_DIR, SAMPLE_RATE, FEATURE_TYPE, N_MELS, MEL_MAX_LEN,
    N_MFCC, MFCC_MAX_LEN, EPOCHS, BATCH_SIZE,
    LEARNING_RATE, VALIDATION_SPLIT, DROPOUT_RATE,
    INPUT_SHAPE_MEL, INPUT_SHAPE_MFCC
)
from utils.helpers import (
    setup_logger, ensure_directories, pad_or_truncate
)
from feature_extraction import extract_features, load_audio_file

logger = setup_logger("ModelTraining")

# ============================================================
# URBANSOUND8K CLASS-TO-DISTRESS MAPPING
# ============================================================
# Classes that represent distress/danger/emergency sounds
DISTRESS_CLASS_IDS = {6, 8}       # gun_shot, siren
# Classes that represent normal everyday sounds
NORMAL_CLASS_IDS = {0, 2, 3, 4, 5, 7, 9}
# car_horn (1) is ambiguous — exclude from training to avoid confusion
EXCLUDED_CLASS_IDS = {1}

URBAN_CLASS_NAMES = {
    0: "air_conditioner", 1: "car_horn", 2: "children_playing",
    3: "dog_bark", 4: "drilling", 5: "engine_idling",
    6: "gun_shot", 7: "jackhammer", 8: "siren", 9: "street_music"
}


def load_urbansound8k():
    """
    Load UrbanSound8K dataset from dataset/urban/ directory.
    Maps the 10-class dataset into binary distress/normal labels.

    Returns:
        Tuple of (features_array, labels_array)
    """
    urban_dir = os.path.join(DATASET_DIR, "urban")
    csv_path = os.path.join(urban_dir, "UrbanSound8K.csv")

    if not os.path.exists(csv_path):
        logger.error(f"UrbanSound8K.csv not found at {csv_path}")
        sys.exit(1)

    # Parse the CSV metadata
    logger.info(f"Reading UrbanSound8K metadata from {csv_path}")
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        metadata = list(reader)

    logger.info(f"  Total entries in CSV: {len(metadata)}")

    # Count classes
    distress_count = sum(1 for r in metadata if int(r["classID"]) in DISTRESS_CLASS_IDS)
    normal_count = sum(1 for r in metadata if int(r["classID"]) in NORMAL_CLASS_IDS)
    excluded_count = sum(1 for r in metadata if int(r["classID"]) in EXCLUDED_CLASS_IDS)

    logger.info(f"\n  Class mapping:")
    logger.info(f"    DISTRESS classes: {', '.join(URBAN_CLASS_NAMES[c] for c in sorted(DISTRESS_CLASS_IDS))}")
    logger.info(f"    NORMAL classes:   {', '.join(URBAN_CLASS_NAMES[c] for c in sorted(NORMAL_CLASS_IDS))}")
    logger.info(f"    EXCLUDED classes: {', '.join(URBAN_CLASS_NAMES[c] for c in sorted(EXCLUDED_CLASS_IDS))}")
    logger.info(f"\n    Distress samples: {distress_count}")
    logger.info(f"    Normal samples:   {normal_count}")
    logger.info(f"    Excluded samples: {excluded_count}")

    # Balance the dataset: undersample normal class to match distress count
    # This prevents the model from being biased toward "normal"
    # We take a proportional random sample of normal entries
    max_per_class = distress_count  # ~1303 (gun_shot + siren)
    logger.info(f"\n  Balancing: using {max_per_class} samples per class")

    # Separate entries by label
    distress_entries = [r for r in metadata if int(r["classID"]) in DISTRESS_CLASS_IDS]
    normal_entries = [r for r in metadata if int(r["classID"]) in NORMAL_CLASS_IDS]

    # Shuffle and take balanced sample of normal entries
    np.random.seed(42)
    np.random.shuffle(normal_entries)
    normal_entries = normal_entries[:max_per_class]

    all_entries = distress_entries + normal_entries
    np.random.shuffle(all_entries)

    logger.info(f"  Total samples to process: {len(all_entries)}")

    features_list = []
    labels_list = []
    errors = 0

    for i, row in enumerate(all_entries):
        fold = row["fold"]
        filename = row["slice_file_name"]
        class_id = int(row["classID"])
        filepath = os.path.join(urban_dir, f"fold{fold}", filename)

        if not os.path.exists(filepath):
            errors += 1
            continue

        # Load audio
        audio, sr = load_audio_file(filepath)
        if audio is None:
            errors += 1
            continue

        # Pad/truncate to consistent chunk length
        audio = pad_or_truncate(audio)

        # Extract features
        try:
            feat = extract_features(audio, sr)
            features_list.append(feat)

            # Binary label
            if class_id in DISTRESS_CLASS_IDS:
                labels_list.append(1)  # Distress
            else:
                labels_list.append(0)  # Normal
        except Exception as e:
            errors += 1
            continue

        if (i + 1) % 200 == 0:
            logger.info(f"  Processed {i + 1}/{len(all_entries)} files...")

    if errors > 0:
        logger.warning(f"  Skipped {errors} files due to errors")

    X = np.array(features_list)
    y = np.array(labels_list)
    X = X[..., np.newaxis]  # Add channel dim: (N, H, W) -> (N, H, W, 1)

    logger.info(f"\n  Dataset loaded:")
    logger.info(f"    Total:    {len(y)}")
    logger.info(f"    Distress: {np.sum(y == 1)}")
    logger.info(f"    Normal:   {np.sum(y == 0)}")
    logger.info(f"    Shape:    {X.shape}")

    return X, y


def load_custom_dataset():
    """
    Load audio files from dataset/distress/ and dataset/normal/ directories.
    Original approach for custom or synthetic data.

    Returns:
        Tuple of (features_array, labels_array)
    """
    features_list = []
    labels_list = []

    # --- Load Distress Samples (label = 1) ---
    logger.info(f"Loading distress samples from: {DISTRESS_DIR}")
    distress_files = [
        f for f in os.listdir(DISTRESS_DIR)
        if f.endswith(('.wav', '.mp3', '.ogg', '.flac'))
    ]
    logger.info(f"  Found {len(distress_files)} distress files")

    for i, filename in enumerate(distress_files):
        filepath = os.path.join(DISTRESS_DIR, filename)
        audio, sr = load_audio_file(filepath)

        if audio is not None:
            audio = pad_or_truncate(audio)
            feat = extract_features(audio, sr)
            features_list.append(feat)
            labels_list.append(1)

        if (i + 1) % 25 == 0:
            logger.info(f"  Processed {i + 1}/{len(distress_files)} distress files")

    # --- Load Normal Samples (label = 0) ---
    logger.info(f"Loading normal samples from: {NORMAL_DIR}")
    normal_files = [
        f for f in os.listdir(NORMAL_DIR)
        if f.endswith(('.wav', '.mp3', '.ogg', '.flac'))
    ]
    logger.info(f"  Found {len(normal_files)} normal files")

    for i, filename in enumerate(normal_files):
        filepath = os.path.join(NORMAL_DIR, filename)
        audio, sr = load_audio_file(filepath)

        if audio is not None:
            audio = pad_or_truncate(audio)
            feat = extract_features(audio, sr)
            features_list.append(feat)
            labels_list.append(0)

        if (i + 1) % 25 == 0:
            logger.info(f"  Processed {i + 1}/{len(normal_files)} normal files")

    if len(features_list) == 0:
        logger.error("No audio files found!")
        sys.exit(1)

    X = np.array(features_list)
    y = np.array(labels_list)
    X = X[..., np.newaxis]

    logger.info(f"\n  Dataset loaded:")
    logger.info(f"    Total:    {len(y)}")
    logger.info(f"    Distress: {np.sum(y == 1)}")
    logger.info(f"    Normal:   {np.sum(y == 0)}")
    logger.info(f"    Shape:    {X.shape}")

    return X, y


def build_model(input_shape):
    """
    Build the CNN binary classification model.

    Architecture:
        Conv2D(32) -> BatchNorm -> MaxPool ->
        Conv2D(64) -> BatchNorm -> MaxPool ->
        Conv2D(128) -> BatchNorm -> MaxPool ->
        GlobalAveragePooling2D ->
        Dense(128) -> Dropout(0.5) ->
        Dense(64) -> Dropout(0.3) ->
        Dense(1, sigmoid)

    Deeper dense layers + stronger dropout to combat overfitting
    on the larger UrbanSound8K dataset.
    """
    model = keras.Sequential([
        # --- Block 1 ---
        layers.Conv2D(32, (3, 3), activation='relu', padding='same',
                      input_shape=input_shape, name='conv1'),
        layers.BatchNormalization(name='bn1'),
        layers.MaxPooling2D((2, 2), name='pool1'),

        # --- Block 2 ---
        layers.Conv2D(64, (3, 3), activation='relu', padding='same',
                      name='conv2'),
        layers.BatchNormalization(name='bn2'),
        layers.MaxPooling2D((2, 2), name='pool2'),

        # --- Block 3 ---
        layers.Conv2D(128, (3, 3), activation='relu', padding='same',
                      name='conv3'),
        layers.BatchNormalization(name='bn3'),
        layers.MaxPooling2D((2, 2), name='pool3'),

        # --- Classification Head ---
        layers.GlobalAveragePooling2D(name='global_pool'),
        layers.Dense(128, activation='relu', name='dense1'),
        layers.Dropout(0.5, name='dropout1'),
        layers.Dense(64, activation='relu', name='dense2'),
        layers.Dropout(DROPOUT_RATE, name='dropout2'),
        layers.Dense(1, activation='sigmoid', name='output')
    ], name='ASAAP_DistressClassifier')

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model


def normalize_features(X_train, X_val):
    """
    Standardize features to zero mean and unit variance.
    Computed on training set and applied to both train and val.
    Saves mean/std for inference-time normalization.

    Returns:
        (X_train_norm, X_val_norm, mean, std)
    """
    # Compute per-channel mean and std across all training samples
    mean = np.mean(X_train, axis=0)
    std = np.std(X_train, axis=0)
    std[std == 0] = 1.0  # Prevent division by zero

    X_train_norm = (X_train - mean) / std
    X_val_norm = (X_val - mean) / std

    return X_train_norm, X_val_norm, mean, std


def train():
    """
    Full training pipeline:
    1. Detect and load dataset (UrbanSound8K or custom)
    2. Split into train/validation
    3. Normalize features
    4. Build and train CNN model
    5. Evaluate on validation set
    6. Save trained model + normalization stats
    """
    logger.info("=" * 60)
    logger.info("ASAAP - Model Training Pipeline")
    logger.info("=" * 60)

    ensure_directories()

    # --- Step 1: Detect and load dataset ---
    use_urban = "--urban" in sys.argv
    use_custom = "--custom" in sys.argv

    urban_dir = os.path.join(DATASET_DIR, "urban")
    urban_csv = os.path.join(urban_dir, "UrbanSound8K.csv")

    if use_custom:
        logger.info("\nStep 1: Loading CUSTOM dataset (--custom flag)...")
        X, y = load_custom_dataset()
    elif use_urban or os.path.exists(urban_csv):
        logger.info("\nStep 1: Loading URBANSOUND8K dataset...")
        X, y = load_urbansound8k()
    else:
        logger.info("\nStep 1: Loading CUSTOM dataset...")
        X, y = load_custom_dataset()

    # --- Step 2: Train/Validation split ---
    logger.info("\nStep 2: Splitting dataset...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=VALIDATION_SPLIT,
        random_state=42,
        stratify=y
    )
    logger.info(f"  Training:   {len(y_train)} samples (distress={np.sum(y_train==1)}, normal={np.sum(y_train==0)})")
    logger.info(f"  Validation: {len(y_val)} samples (distress={np.sum(y_val==1)}, normal={np.sum(y_val==0)})")

    # --- Step 3: Normalize features ---
    logger.info("\nStep 3: Normalizing features (zero mean, unit variance)...")
    X_train, X_val, feat_mean, feat_std = normalize_features(X_train, X_val)
    logger.info(f"  Feature range after norm: [{X_train.min():.2f}, {X_train.max():.2f}]")

    # Save normalization stats for inference
    norm_path = os.path.join(MODELS_DIR, "norm_stats.npz")
    np.savez(norm_path, mean=feat_mean, std=feat_std)
    logger.info(f"  Normalization stats saved to {norm_path}")

    # --- Step 4: Build model ---
    logger.info("\nStep 4: Building CNN model...")
    input_shape = X_train.shape[1:]  # (H, W, 1)
    model = build_model(input_shape)
    model.summary(print_fn=logger.info)

    # --- Step 5: Train model ---
    logger.info(f"\nStep 5: Training for up to {EPOCHS} epochs...")

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=7,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1
        )
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )

    # --- Step 6: Evaluate model ---
    logger.info("\nStep 6: Evaluating model...")

    y_pred_prob = model.predict(X_val, verbose=0)
    y_pred = (y_pred_prob > 0.5).astype(int).flatten()

    report = classification_report(
        y_val, y_pred,
        target_names=['Normal', 'Distress'],
        digits=4
    )
    logger.info(f"\nClassification Report:\n{report}")

    cm = confusion_matrix(y_val, y_pred)
    logger.info(f"Confusion Matrix:")
    logger.info(f"  TN={cm[0][0]}  FP={cm[0][1]}")
    logger.info(f"  FN={cm[1][0]}  TP={cm[1][1]}")

    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    logger.info(f"\nFinal Validation Loss: {val_loss:.4f}")
    logger.info(f"Final Validation Accuracy: {val_acc:.4f}")

    # --- Step 7: Save model ---
    logger.info(f"\nStep 7: Saving model to {MODEL_SAVE_PATH}...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    model.save(MODEL_SAVE_PATH)
    logger.info(f"  Model saved successfully!")

    logger.info("\n" + "=" * 60)
    logger.info("Training pipeline complete!")
    logger.info("=" * 60)

    return model, history


if __name__ == "__main__":
    train()
