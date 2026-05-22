"""
ASAAP - Anti Sexual Abuse Alerting Program
Synthetic Dataset Generator

Generates synthetic audio samples for training when real datasets
are not available. Creates two classes:
  - "distress": High-frequency tones, amplitude spikes, frequency
                 sweeps simulating screams/cries/panic
  - "normal":   Low-frequency hums, gentle ambient noise, steady
                 tones simulating normal environment sounds

IMPORTANT: This synthetic data is for MVP demonstration only.
For production accuracy, replace with real labeled audio data
from datasets like UrbanSound8K, ESC-50, or custom recordings.

Usage:
    python dataset/generate_synthetic.py
"""

import os
import sys
import numpy as np
from scipy.io import wavfile

# Add project root to path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    SAMPLE_RATE, SYNTHETIC_COUNT_PER_CLASS,
    SYNTHETIC_DURATION, DISTRESS_DIR, NORMAL_DIR
)
from utils.helpers import setup_logger, ensure_directories, normalize_audio

logger = setup_logger("SyntheticDataGen")


def generate_scream_like(duration: float, sr: int) -> np.ndarray:
    """
    Generate audio resembling a scream: high-frequency with
    rapid amplitude modulation and frequency sweeps.
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # High-frequency carrier (800-2000 Hz range, typical of screams)
    base_freq = np.random.uniform(800, 2000)

    # Frequency sweep (simulates rising pitch in a scream)
    sweep = np.linspace(base_freq, base_freq * np.random.uniform(1.2, 2.0), len(t))
    carrier = np.sin(2 * np.pi * sweep * t)

    # Amplitude modulation (pulsing/trembling effect)
    mod_freq = np.random.uniform(5, 15)
    modulator = 0.5 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
    signal = carrier * modulator

    # Add harmonics for richer tone
    harmonic = 0.3 * np.sin(2 * np.pi * sweep * 2 * t)
    signal += harmonic

    # Add noise burst
    noise = np.random.normal(0, np.random.uniform(0.1, 0.3), len(t)).astype(np.float32)
    signal += noise

    # Random amplitude envelope (sudden onset)
    attack = np.minimum(t / 0.05, 1.0)  # 50ms attack
    signal *= attack

    return normalize_audio(signal)


def generate_cry_like(duration: float, sr: int) -> np.ndarray:
    """
    Generate audio resembling crying: irregular pitch with
    periodic sobbing pattern.
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # Crying typically 250-600 Hz
    base_freq = np.random.uniform(250, 600)

    # Sobbing pattern: periodic amplitude drops
    sob_freq = np.random.uniform(1.5, 4.0)  # sobs per second
    sob_pattern = 0.3 + 0.7 * np.abs(np.sin(2 * np.pi * sob_freq * t))

    # Slightly unsteady pitch (vibrato)
    vibrato = base_freq + 30 * np.sin(2 * np.pi * 5 * t)
    carrier = np.sin(2 * np.pi * vibrato * t)

    signal = carrier * sob_pattern

    # Add breathiness (noise component)
    breath_noise = np.random.normal(0, 0.15, len(t)).astype(np.float32)
    signal += breath_noise * sob_pattern

    return normalize_audio(signal)


def generate_panic_voice(duration: float, sr: int) -> np.ndarray:
    """
    Generate audio resembling panicked speech: fast pitch
    variations with high energy.
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # Panicked voice: higher than normal speech
    base_freq = np.random.uniform(300, 800)

    # Rapid pitch changes
    pitch_var = base_freq + 100 * np.sin(2 * np.pi * np.random.uniform(3, 8) * t)
    carrier = np.sin(2 * np.pi * pitch_var * t)

    # Intensity bursts
    bursts = np.random.uniform(0.5, 1.0, len(t)).astype(np.float32)
    # Smooth the bursts
    from scipy.ndimage import uniform_filter1d
    bursts = uniform_filter1d(bursts, size=int(sr * 0.1))

    signal = carrier * bursts

    # Add some noise for realism
    noise = np.random.normal(0, 0.2, len(t)).astype(np.float32)
    signal += noise

    return normalize_audio(signal)


def generate_help_call(duration: float, sr: int) -> np.ndarray:
    """
    Generate audio resembling "help" calls: repeated tonal bursts
    with pauses between them.
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)
    signal = np.zeros_like(t)

    # Create 2-4 burst segments (like repeated "help!" calls)
    num_bursts = np.random.randint(2, 5)
    burst_duration = duration / (num_bursts * 2)

    for i in range(num_bursts):
        start_idx = int(i * 2 * burst_duration * sr)
        end_idx = int((i * 2 + 1) * burst_duration * sr)
        if end_idx > len(t):
            end_idx = len(t)

        burst_len = end_idx - start_idx
        burst_t = np.linspace(0, burst_duration, burst_len, dtype=np.float32)

        # Each burst is a high-pitched tone
        freq = np.random.uniform(500, 1200)
        burst = np.sin(2 * np.pi * freq * burst_t)

        # Sharp attack and decay envelope
        envelope = np.exp(-3 * np.abs(burst_t - burst_duration / 2) / burst_duration)
        signal[start_idx:end_idx] = burst * envelope

    # Add ambient noise
    noise = np.random.normal(0, 0.1, len(t)).astype(np.float32)
    signal += noise

    return normalize_audio(signal)


def generate_normal_ambient(duration: float, sr: int) -> np.ndarray:
    """
    Generate normal ambient sound: low-frequency hum with
    gentle background noise (office, street, home environment).
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # Low-frequency hum (50-200 Hz — like electronics, AC, etc.)
    hum_freq = np.random.uniform(50, 200)
    hum = 0.3 * np.sin(2 * np.pi * hum_freq * t)

    # Gentle background noise
    noise_level = np.random.uniform(0.02, 0.1)
    noise = np.random.normal(0, noise_level, len(t)).astype(np.float32)

    signal = hum + noise

    return normalize_audio(signal) * 0.3  # Keep amplitude low


def generate_normal_speech_like(duration: float, sr: int) -> np.ndarray:
    """
    Generate sound resembling calm normal speech: steady pitch,
    moderate frequency, low energy.
    """
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # Normal speech fundamental: 85-255 Hz
    base_freq = np.random.uniform(100, 250)

    # Gentle pitch variation (natural speech intonation)
    pitch = base_freq + 20 * np.sin(2 * np.pi * 0.5 * t)
    carrier = np.sin(2 * np.pi * pitch * t)

    # Smooth amplitude envelope (conversational rhythm)
    envelope = 0.5 + 0.3 * np.sin(2 * np.pi * np.random.uniform(1, 3) * t)
    signal = carrier * envelope * 0.4

    # Add slight noise
    noise = np.random.normal(0, 0.05, len(t)).astype(np.float32)
    signal += noise

    return normalize_audio(signal) * 0.4


def generate_silence_with_noise(duration: float, sr: int) -> np.ndarray:
    """
    Generate near-silence with very faint background noise.
    Represents quiet room environments.
    """
    n_samples = int(sr * duration)
    noise_level = np.random.uniform(0.005, 0.03)
    signal = np.random.normal(0, noise_level, n_samples).astype(np.float32)
    return signal


def generate_dataset():
    """
    Generate the full synthetic dataset.
    Creates distress and normal audio samples as .wav files.
    """
    ensure_directories()

    logger.info("=" * 60)
    logger.info("ASAAP — Synthetic Dataset Generator")
    logger.info("=" * 60)
    logger.info(f"Samples per class: {SYNTHETIC_COUNT_PER_CLASS}")
    logger.info(f"Duration per sample: {SYNTHETIC_DURATION}s")
    logger.info(f"Sample rate: {SAMPLE_RATE} Hz")
    logger.info(f"Output: {DISTRESS_DIR}")
    logger.info(f"         {NORMAL_DIR}")
    logger.info("=" * 60)

    # --- Generate Distress Samples ---
    logger.info("\n🔴 Generating DISTRESS samples...")
    distress_generators = [
        ("scream", generate_scream_like),
        ("cry", generate_cry_like),
        ("panic", generate_panic_voice),
        ("help_call", generate_help_call),
    ]

    for i in range(SYNTHETIC_COUNT_PER_CLASS):
        # Cycle through distress types
        gen_name, gen_func = distress_generators[i % len(distress_generators)]
        audio = gen_func(SYNTHETIC_DURATION, SAMPLE_RATE)

        # Convert to int16 for WAV file
        audio_int16 = (audio * 32767).astype(np.int16)

        filename = f"distress_{gen_name}_{i:04d}.wav"
        filepath = os.path.join(DISTRESS_DIR, filename)
        wavfile.write(filepath, SAMPLE_RATE, audio_int16)

        if (i + 1) % 25 == 0:
            logger.info(f"  Generated {i + 1}/{SYNTHETIC_COUNT_PER_CLASS} distress samples")

    logger.info(f"  ✅ {SYNTHETIC_COUNT_PER_CLASS} distress samples saved")

    # --- Generate Normal Samples ---
    logger.info("\n🟢 Generating NORMAL samples...")
    normal_generators = [
        ("ambient", generate_normal_ambient),
        ("speech", generate_normal_speech_like),
        ("silence", generate_silence_with_noise),
    ]

    for i in range(SYNTHETIC_COUNT_PER_CLASS):
        # Cycle through normal types
        gen_name, gen_func = normal_generators[i % len(normal_generators)]
        audio = gen_func(SYNTHETIC_DURATION, SAMPLE_RATE)

        # Convert to int16 for WAV file
        audio_int16 = (audio * 32767).astype(np.int16)

        filename = f"normal_{gen_name}_{i:04d}.wav"
        filepath = os.path.join(NORMAL_DIR, filename)
        wavfile.write(filepath, SAMPLE_RATE, audio_int16)

        if (i + 1) % 25 == 0:
            logger.info(f"  Generated {i + 1}/{SYNTHETIC_COUNT_PER_CLASS} normal samples")

    logger.info(f"  ✅ {SYNTHETIC_COUNT_PER_CLASS} normal samples saved")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Synthetic dataset generation complete!")
    logger.info(f"Total samples: {SYNTHETIC_COUNT_PER_CLASS * 2}")
    logger.info("=" * 60)
    logger.info("\n💡 TIP: For better accuracy, replace synthetic data with")
    logger.info("   real audio from UrbanSound8K, ESC-50, or custom recordings.")


if __name__ == "__main__":
    generate_dataset()
