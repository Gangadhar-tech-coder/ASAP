"""
ASAAP - Anti Sexual Abuse Alerting Program
Real-Time Audio Stream Module

Captures microphone audio in real-time using sounddevice,
accumulates samples into fixed-duration chunks, and pushes
completed chunks to a thread-safe queue for inference.

Privacy: Audio is kept in memory only. Chunks are discarded
after processing. No audio is ever written to disk.
"""

import numpy as np
import sounddevice as sd
import queue
import threading

from utils.config import SAMPLE_RATE, CHUNK_SAMPLES, CHANNELS
from utils.helpers import setup_logger

logger = setup_logger("AudioStream")


class AudioStream:
    """
    Real-time microphone audio capture with chunk buffering.
    
    Continuously captures audio from the default microphone,
    accumulates samples into fixed-size chunks, and places
    completed chunks into a queue for the inference engine.
    
    Usage:
        stream = AudioStream()
        stream.start()
        
        while monitoring:
            chunk = stream.get_chunk(timeout=1.0)
            if chunk is not None:
                process(chunk)
        
        stream.stop()
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE,
                 chunk_samples: int = CHUNK_SAMPLES,
                 channels: int = CHANNELS):
        """
        Initialize the audio stream.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_samples: Number of samples per chunk
            channels: Number of audio channels (1 = mono)
        """
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples
        self.channels = channels

        # Thread-safe queue for completed audio chunks
        self.chunk_queue = queue.Queue(maxsize=10)

        # Buffer to accumulate incoming audio samples
        self._buffer = np.array([], dtype=np.float32)
        self._buffer_lock = threading.Lock()

        # Stream state
        self._stream = None
        self._is_running = False

        logger.info(f"AudioStream initialized: {sample_rate}Hz, "
                     f"{chunk_samples} samples/chunk "
                     f"({chunk_samples / sample_rate:.1f}s)")

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function called by sounddevice for each audio block.
        Accumulates samples and emits chunks when buffer is full.
        
        Args:
            indata: Input audio data (numpy array)
            frames: Number of frames
            time_info: Timing information
            status: Stream status flags
        """
        if status:
            logger.warning(f"Audio stream status: {status}")

        # Extract mono channel and flatten
        audio_data = indata[:, 0].copy().astype(np.float32)

        with self._buffer_lock:
            # Append new data to buffer
            self._buffer = np.concatenate([self._buffer, audio_data])

            # Emit complete chunks
            while len(self._buffer) >= self.chunk_samples:
                chunk = self._buffer[:self.chunk_samples].copy()
                self._buffer = self._buffer[self.chunk_samples:]

                try:
                    # Non-blocking put — drop oldest if queue is full
                    if self.chunk_queue.full():
                        try:
                            self.chunk_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self.chunk_queue.put_nowait(chunk)
                except queue.Full:
                    logger.warning("Chunk queue full, dropping chunk")

    def start(self):
        """
        Start capturing audio from the microphone.
        Opens the audio stream in a background thread.
        """
        if self._is_running:
            logger.warning("Audio stream already running")
            return

        try:
            # Clear any old data
            with self._buffer_lock:
                self._buffer = np.array([], dtype=np.float32)
            
            # Clear the queue
            while not self.chunk_queue.empty():
                try:
                    self.chunk_queue.get_nowait()
                except queue.Empty:
                    break

            # Open the input stream
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=1024,  # Small blocks for low latency
                callback=self._audio_callback
            )
            self._stream.start()
            self._is_running = True
            logger.info("🎤 Microphone capture started")

        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self._is_running = False
            raise

    def stop(self):
        """
        Stop capturing audio and release the microphone.
        """
        if not self._is_running:
            return

        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            self._is_running = False

            # Clear buffer (privacy: don't hold audio data)
            with self._buffer_lock:
                self._buffer = np.array([], dtype=np.float32)

            logger.info("🛑 Microphone capture stopped")

        except Exception as e:
            logger.error(f"Error stopping audio stream: {e}")

    def get_chunk(self, timeout: float = 1.0):
        """
        Get the next complete audio chunk from the queue.
        Blocks until a chunk is available or timeout expires.
        
        Args:
            timeout: Maximum seconds to wait for a chunk
        
        Returns:
            numpy array of audio samples, or None if timeout
        """
        try:
            chunk = self.chunk_queue.get(timeout=timeout)
            return chunk
        except queue.Empty:
            return None

    @property
    def is_running(self) -> bool:
        """Check if the audio stream is currently active."""
        return self._is_running

    def get_audio_devices(self):
        """
        List available audio input devices.
        Useful for debugging microphone issues.
        
        Returns:
            List of input device info dictionaries
        """
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': dev['name'],
                    'channels': dev['max_input_channels'],
                    'sample_rate': dev['default_samplerate']
                })
        return input_devices
