"""
ASAAP - Anti Sexual Abuse Alerting Program
Alert System Module

Handles all alert actions when distress is detected:
- Visual popup alert with timestamp
- Audible alarm sound (generated programmatically)
- Simulated emergency email notification
- GPS location simulation
- Detection event history logging
"""

import numpy as np
import sounddevice as sd
import threading
import smtplib
import random
import math
from email.mime.text import MIMEText
from datetime import datetime

from utils.config import (
    ALARM_DURATION, ALARM_FREQUENCY, SAMPLE_RATE,
    EMAIL_ENABLED, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT,
    GPS_BASE_LAT, GPS_BASE_LON, GPS_RADIUS_KM
)
from utils.helpers import setup_logger, get_timestamp

logger = setup_logger("AlertSystem")


class AlertSystem:
    """
    Manages all alert actions for the ASAAP system.
    
    When distress is detected, this system can:
    1. Play an alarm sound
    2. Display alert information
    3. Send email notifications (simulated or real)
    4. Generate simulated GPS coordinates
    5. Maintain a history of detection events
    
    All actions are non-blocking (run in separate threads)
    to avoid freezing the main application.
    """

    def __init__(self):
        """Initialize the alert system with empty event history."""
        # History of detection events
        self.event_history = []

        # Track if alarm is currently playing
        self._alarm_playing = False
        self._alarm_thread = None

        logger.info("AlertSystem initialized")

    def trigger_alert(self, confidence: float, callback=None):
        """
        Trigger a full alert sequence.
        
        This is the main entry point called when distress is
        confirmed by the detection engine.
        
        Args:
            confidence: Detection confidence (0.0 to 1.0)
            callback: Optional GUI callback for popup display
        """
        timestamp = get_timestamp()
        gps = self.simulate_gps()

        # Create event record
        event = {
            "timestamp": timestamp,
            "confidence": confidence,
            "gps_lat": gps["latitude"],
            "gps_lon": gps["longitude"],
            "alert_sent": True
        }
        self.event_history.append(event)

        logger.warning("=" * 50)
        logger.warning("🚨 DISTRESS ALERT TRIGGERED!")
        logger.warning(f"   Time: {timestamp}")
        logger.warning(f"   Confidence: {confidence:.2%}")
        logger.warning(f"   Location: {gps['latitude']:.6f}, {gps['longitude']:.6f}")
        logger.warning("=" * 50)

        # Play alarm sound (non-blocking)
        self.play_alarm()

        # Send email alert (non-blocking)
        self._send_email_async(event)

        # Call GUI callback if provided
        if callback:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"GUI callback error: {e}")

    def play_alarm(self):
        """
        Play a loud alarm tone using generated sine wave.
        Runs in a separate thread to avoid blocking.
        """
        if self._alarm_playing:
            return  # Don't stack alarms

        def _play():
            try:
                self._alarm_playing = True

                # Generate alarm tone: alternating frequencies for urgency
                t = np.linspace(
                    0, ALARM_DURATION,
                    int(SAMPLE_RATE * ALARM_DURATION),
                    dtype=np.float32
                )

                # Two-tone alarm (like a siren)
                freq1 = ALARM_FREQUENCY        # 880 Hz
                freq2 = ALARM_FREQUENCY * 1.5   # 1320 Hz

                # Switch between frequencies rapidly
                switch_rate = 4  # switches per second
                selector = (np.sin(2 * np.pi * switch_rate * t) > 0).astype(np.float32)
                tone1 = np.sin(2 * np.pi * freq1 * t) * selector
                tone2 = np.sin(2 * np.pi * freq2 * t) * (1 - selector)
                alarm = (tone1 + tone2) * 0.7  # 70% volume

                # Play the alarm
                sd.play(alarm, samplerate=SAMPLE_RATE)
                sd.wait()

                self._alarm_playing = False

            except Exception as e:
                logger.error(f"Alarm playback error: {e}")
                self._alarm_playing = False

        self._alarm_thread = threading.Thread(target=_play, daemon=True)
        self._alarm_thread.start()

    def stop_alarm(self):
        """Stop any currently playing alarm."""
        try:
            sd.stop()
            self._alarm_playing = False
        except Exception:
            pass

    def simulate_gps(self) -> dict:
        """
        Generate simulated GPS coordinates near the base location.
        In a real app, this would use actual GPS hardware or phone API.
        
        Returns:
            Dictionary with 'latitude' and 'longitude'
        """
        # Random offset within GPS_RADIUS_KM
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 * cos(latitude) km
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, GPS_RADIUS_KM)

        delta_lat = (distance / 111.0) * math.cos(angle)
        delta_lon = (distance / (111.0 * math.cos(math.radians(GPS_BASE_LAT)))) * math.sin(angle)

        return {
            "latitude": GPS_BASE_LAT + delta_lat,
            "longitude": GPS_BASE_LON + delta_lon
        }

    def _send_email_async(self, event: dict):
        """
        Send email alert in a background thread.
        Simulated by default — set EMAIL_ENABLED=True in config
        and provide credentials for real email.
        
        Args:
            event: Detection event dictionary
        """
        def _send():
            if EMAIL_ENABLED:
                self._send_real_email(event)
            else:
                self._simulate_email(event)

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

    def _simulate_email(self, event: dict):
        """
        Simulate sending an emergency email (log only).
        """
        logger.info("📧 [SIMULATED] Emergency email would be sent:")
        logger.info(f"   To: emergency_contact@example.com")
        logger.info(f"   Subject: 🚨 ASAAP DISTRESS ALERT")
        logger.info(f"   Body: Distress detected at {event['timestamp']}")
        logger.info(f"         Confidence: {event['confidence']:.2%}")
        logger.info(f"         GPS: {event['gps_lat']:.6f}, {event['gps_lon']:.6f}")
        logger.info(f"   Status: Email simulation logged (enable real email in config)")

    def _send_real_email(self, event: dict):
        """
        Actually send an emergency email via SMTP.
        Requires valid credentials in config.
        
        Args:
            event: Detection event dictionary
        """
        try:
            subject = "🚨 ASAAP DISTRESS ALERT — Immediate Attention Required"
            body = f"""
⚠️ ASAAP — DISTRESS ALERT ⚠️

A potential distress situation has been detected.

Details:
  • Timestamp: {event['timestamp']}
  • Confidence: {event['confidence']:.2%}
  • Estimated Location: {event['gps_lat']:.6f}, {event['gps_lon']:.6f}
  • Google Maps: https://maps.google.com/?q={event['gps_lat']},{event['gps_lon']}

This is an automated alert from ASAAP (Anti Sexual Abuse Alerting Program).
Please verify and take appropriate action.
            """

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_SENDER
            msg['To'] = EMAIL_RECIPIENT

            with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

            logger.info(f"📧 Emergency email sent to {EMAIL_RECIPIENT}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def get_event_history(self) -> list:
        """
        Get the full history of detection events.
        
        Returns:
            List of event dictionaries (newest last)
        """
        return self.event_history.copy()

    def get_last_event(self) -> dict:
        """
        Get the most recent detection event.
        
        Returns:
            Last event dictionary, or None if no events
        """
        if self.event_history:
            return self.event_history[-1]
        return None

    def clear_history(self):
        """Clear the event history."""
        self.event_history.clear()
        logger.info("Event history cleared")
