# 🛡️ ASAAP — Anti Sexual Abuse Alerting Program

> **AI-Powered Passive Distress Detection System for Women Safety**

ASAAP is a real-time passive safety monitoring application that continuously captures microphone audio, detects distress sounds (screams, crying, panic voice, help calls) using a CNN-based AI model, and automatically triggers emergency alerts — all without requiring any user interaction.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Passive Monitoring** | Continuously listens to microphone audio in real-time |
| 🧠 **AI Distress Detection** | CNN classifier identifies screams, cries, panic, help calls |
| 🚨 **Automatic Alerts** | Popup + alarm sound + simulated email when distress detected |
| 📊 **Live Confidence Meter** | Real-time visualization of detection confidence |
| 🎚️ **Sensitivity Slider** | Adjustable detection threshold to control sensitivity |
| 📋 **Detection Log** | Timestamped event history for all detections |
| 🔒 **Privacy-First** | Audio is never saved to disk — processed in memory only |
| 📧 **Email Alerts** | Simulated (or real SMTP) emergency notifications |
| 📍 **GPS Simulation** | Simulated location coordinates with Google Maps links |
| 🌙 **Dark Theme UI** | Modern CustomTkinter interface with sleek dark mode |

---

## 📂 Project Structure

```
ASAAP/
├── app.py                     # Main GUI application
├── train_model.py             # CNN training pipeline
├── predict.py                 # Real-time inference engine
├── audio_stream.py            # Microphone audio capture
├── feature_extraction.py      # MFCC / Mel Spectrogram extraction
├── alert_system.py            # Alerts: popup, alarm, email, GPS
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── dataset/
│   ├── generate_synthetic.py  # Synthetic training data generator
│   ├── distress/              # Distress audio samples (.wav)
│   └── normal/                # Normal audio samples (.wav)
│
├── models/
│   └── asaap_model.keras      # Saved trained model
│
└── utils/
    ├── __init__.py
    ├── config.py              # Central configuration
    └── helpers.py             # Shared utility functions
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** TensorFlow installation may take a few minutes. On Windows, ensure you have Python 3.9-3.11.

### 2. Generate Synthetic Dataset

```bash
python dataset/generate_synthetic.py
```

This creates 200 synthetic audio samples (100 distress + 100 normal) for training. For better accuracy, replace with real audio data (see [Dataset Guide](#-dataset-guide) below).

### 3. Train the Model

```bash
python train_model.py
```

The trained CNN model will be saved to `models/asaap_model.keras`.

### 4. Launch the Application

```bash
python app.py
```

The ASAAP GUI will open. Click **"Start Monitoring"** to begin real-time distress detection.

---

## 🧠 How It Works

### Architecture

```
Microphone → Audio Chunks (2.5s) → Feature Extraction → CNN Model → Detection Logic → Alert
```

1. **Audio Capture**: `sounddevice` captures microphone input in real-time
2. **Chunking**: Audio is split into 2.5-second chunks
3. **Feature Extraction**: Each chunk is converted to a Mel Spectrogram (128 bands)
4. **CNN Inference**: The trained model predicts distress probability (0-1)
5. **Validation**: Consecutive distress predictions are tracked to reduce false positives
6. **Alert**: If distress is detected for ≥2 consecutive chunks, an alert triggers

### Detection Logic

```python
distress_count = 0

while monitoring:
    chunk = capture_audio()      # 2.5 seconds
    features = extract_mel(chunk)
    confidence = model.predict(features)

    if confidence > threshold:   # default: 0.80
        distress_count += 1
    else:
        distress_count = 0

    if distress_count >= 2:      # consecutive validation
        trigger_alert()
```

### CNN Model Architecture

```
Input: (128, 109, 1) — Mel Spectrogram
│
├─ Conv2D(32, 3×3, ReLU) → BatchNorm → MaxPool(2×2)
├─ Conv2D(64, 3×3, ReLU) → BatchNorm → MaxPool(2×2)
├─ Conv2D(128, 3×3, ReLU) → BatchNorm → MaxPool(2×2)
├─ GlobalAveragePooling2D
├─ Dense(64, ReLU) → Dropout(0.3)
└─ Dense(1, Sigmoid) — Binary: Normal/Distress
```

---

## 📦 Dataset Guide

### Synthetic Data (Default)

Run `python dataset/generate_synthetic.py` to generate:
- **Distress**: Simulated screams, cries, panic voices, help calls
- **Normal**: Ambient noise, calm speech, silence

### Using Real Datasets

For production-grade accuracy, replace synthetic data with real audio:

#### UrbanSound8K
1. Download from [urbansounddataset.weebly.com](https://urbansounddataset.weebly.com/urbansound8k.html)
2. Copy distress-related classes (e.g., `siren`, `gun_shot`) to `dataset/distress/`
3. Copy non-distress classes to `dataset/normal/`

#### ESC-50
1. Download from [github.com/karolpiczak/ESC-50](https://github.com/karolpiczak/ESC-50)
2. Categorize and copy relevant `.wav` files

#### Custom Dataset
Place your own `.wav` files:
```
dataset/
├── distress/     ← Screams, cries, help calls, panic sounds
└── normal/       ← Speech, ambient noise, silence, music
```

Then retrain: `python train_model.py`

---

## ⚙️ Configuration

All settings are in `utils/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `SAMPLE_RATE` | 22050 | Audio sample rate (Hz) |
| `CHUNK_DURATION` | 2.5 | Seconds per audio chunk |
| `FEATURE_TYPE` | mel_spectrogram | Feature type (mfcc or mel_spectrogram) |
| `CONFIDENCE_THRESHOLD` | 0.80 | Minimum confidence for distress |
| `CONSECUTIVE_THRESHOLD` | 2 | Consecutive detections for alert |
| `EPOCHS` | 30 | Training epochs |
| `BATCH_SIZE` | 16 | Training batch size |

---

## 🔒 Privacy

- ✅ Audio is captured and processed **in memory only**
- ✅ No audio is ever written to disk
- ✅ Chunks are discarded immediately after inference
- ✅ No cloud/internet connection required
- ✅ Runs entirely on your local machine

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module named 'customtkinter'` | Run `pip install customtkinter` |
| `No model found` | Run `python train_model.py` first |
| Microphone not detected | Check Windows Sound Settings → Input |
| TensorFlow GPU errors | Install CPU-only: `pip install tensorflow-cpu` |
| Low detection accuracy | Train with real audio data instead of synthetic |

---

## 📜 License

This project is developed for educational and safety purposes. Use responsibly.

---

## 🙏 Acknowledgments

- **TensorFlow/Keras** — Deep learning framework
- **librosa** — Audio feature extraction
- **CustomTkinter** — Modern Python GUI
- **sounddevice** — Real-time audio capture

---

> **⚠️ Disclaimer**: This is an MVP prototype. For production deployment, thorough testing with diverse real-world audio data is required. This tool is meant to supplement — not replace — existing safety measures.
