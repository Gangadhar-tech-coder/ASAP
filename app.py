"""
ASAAP - Anti Sexual Abuse Alerting Program
Main GUI Application

Modern dark-themed CustomTkinter interface for real-time
passive distress monitoring. Provides:
- Start/Stop monitoring controls
- Live status display with animated indicator
- Real-time confidence meter
- Detection event log
- Sensitivity adjustment slider
- Alert popup on distress detection

Usage:
    python app.py
"""

import customtkinter as ctk
import threading
import time
import sys
import os

from utils.config import (
    APP_TITLE, APP_WIDTH, APP_HEIGHT,
    THEME_MODE, THEME_COLOR,
    CONFIDENCE_THRESHOLD, SAMPLE_RATE
)
from utils.helpers import setup_logger, get_timestamp, ensure_directories
from audio_stream import AudioStream
from predict import DistressDetector
from alert_system import AlertSystem

logger = setup_logger("ASAAP_App")

# ============================================================
# CUSTOMTKINTER GLOBAL SETTINGS
# ============================================================
ctk.set_appearance_mode(THEME_MODE)
ctk.set_default_color_theme(THEME_COLOR)


class ASAAPApp(ctk.CTk):
    """
    Main application window for ASAAP.
    
    Integrates audio capture, ML inference, and alert system
    into a cohesive, modern GUI interface.
    """

    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(850, 600)
        self.resizable(True, True)

        # --- Core Components ---
        self.audio_stream = AudioStream()
        self.detector = DistressDetector()
        self.alert_system = AlertSystem()

        # --- State ---
        self._monitoring = False
        self._monitor_thread = None
        self._pulse_state = False  # For animated indicator

        # --- Build the GUI ---
        self._create_widgets()

        # --- Periodic GUI updates ---
        self._update_pulse()

        # --- Handle window close ---
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        ensure_directories()
        logger.info("ASAAP Application started")

    # ============================================================
    # GUI LAYOUT
    # ============================================================

    def _create_widgets(self):
        """Build the complete GUI layout."""

        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log area expands

        # --- HEADER SECTION ---
        self._create_header()

        # --- CONTROLS SECTION ---
        self._create_controls()

        # --- STATUS SECTION ---
        self._create_status_panel()

        # --- LOG SECTION ---
        self._create_log_panel()

        # --- FOOTER ---
        self._create_footer()

    def _create_header(self):
        """Create the app header with title and branding."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))

        # Shield icon + Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🛡️  ASAAP",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=("#1a73e8", "#60a5fa")
        )
        title_label.pack(side="left")

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Anti Sexual Abuse Alerting Program",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(side="left", padx=(15, 0), pady=(8, 0))

        # Model status indicator (right side)
        model_status = "✅ Model Loaded" if self.detector.model is not None else "⚠️ No Model"
        model_color = ("#22c55e", "#4ade80") if self.detector.model is not None else ("#f59e0b", "#fbbf24")
        self.model_status_label = ctk.CTkLabel(
            header_frame,
            text=model_status,
            font=ctk.CTkFont(size=12),
            text_color=model_color
        )
        self.model_status_label.pack(side="right", padx=10)

    def _create_controls(self):
        """Create the control panel with buttons and sensitivity slider."""
        controls_frame = ctk.CTkFrame(self, corner_radius=12)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        controls_frame.grid_columnconfigure(2, weight=1)

        # Start button
        self.start_btn = ctk.CTkButton(
            controls_frame,
            text="▶  Start Monitoring",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#22c55e", "#16a34a"),
            hover_color=("#16a34a", "#15803d"),
            height=42,
            width=200,
            corner_radius=10,
            command=self._start_monitoring
        )
        self.start_btn.grid(row=0, column=0, padx=(15, 8), pady=15)

        # Stop button
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹  Stop Monitoring",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            height=42,
            width=200,
            corner_radius=10,
            state="disabled",
            command=self._stop_monitoring
        )
        self.stop_btn.grid(row=0, column=1, padx=8, pady=15)

        # Sensitivity slider
        slider_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        slider_frame.grid(row=0, column=2, sticky="e", padx=(20, 15), pady=15)

        slider_label = ctk.CTkLabel(
            slider_frame,
            text="Sensitivity:",
            font=ctk.CTkFont(size=12)
        )
        slider_label.pack(side="left", padx=(0, 8))

        self.sensitivity_slider = ctk.CTkSlider(
            slider_frame,
            from_=0.5,
            to=0.95,
            number_of_steps=9,
            width=150,
            command=self._on_sensitivity_change
        )
        self.sensitivity_slider.set(CONFIDENCE_THRESHOLD)
        self.sensitivity_slider.pack(side="left")

        self.sensitivity_value_label = ctk.CTkLabel(
            slider_frame,
            text=f"{CONFIDENCE_THRESHOLD:.2f}",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=40
        )
        self.sensitivity_value_label.pack(side="left", padx=(8, 0))

    def _create_status_panel(self):
        """Create the status display panel with confidence meter."""
        status_frame = ctk.CTkFrame(self, corner_radius=12)
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)

        # --- Left side: Status indicator ---
        left_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        status_title = ctk.CTkLabel(
            left_frame,
            text="STATUS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray50", "gray60")
        )
        status_title.pack(anchor="w")

        # Animated status indicator
        status_inner = ctk.CTkFrame(left_frame, fg_color="transparent")
        status_inner.pack(anchor="w", pady=(4, 0))

        self.status_dot = ctk.CTkLabel(
            status_inner,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color=("gray50", "gray50"),
            width=25
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            status_inner,
            text="Idle — Ready to monitor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray50", "gray50")
        )
        self.status_label.pack(side="left", padx=(5, 0))

        # --- Center: Confidence display ---
        center_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        center_frame.grid(row=0, column=1, padx=15, pady=15)

        conf_title = ctk.CTkLabel(
            center_frame,
            text="CONFIDENCE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray50", "gray60")
        )
        conf_title.pack()

        self.confidence_label = ctk.CTkLabel(
            center_frame,
            text="0.00",
            font=ctk.CTkFont(family="Consolas", size=36, weight="bold"),
            text_color=("#22c55e", "#4ade80")
        )
        self.confidence_label.pack()

        # Confidence progress bar
        self.confidence_bar = ctk.CTkProgressBar(
            center_frame,
            width=250,
            height=10,
            corner_radius=5,
            progress_color=("#22c55e", "#4ade80")
        )
        self.confidence_bar.set(0)
        self.confidence_bar.pack(pady=(5, 0))

        # --- Right side: Consecutive count ---
        right_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=15, pady=15, sticky="e")

        consec_title = ctk.CTkLabel(
            right_frame,
            text="CONSECUTIVE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray50", "gray60")
        )
        consec_title.pack()

        self.consecutive_label = ctk.CTkLabel(
            right_frame,
            text="0",
            font=ctk.CTkFont(family="Consolas", size=36, weight="bold"),
            text_color=("gray50", "gray50")
        )
        self.consecutive_label.pack()

        consec_sub = ctk.CTkLabel(
            right_frame,
            text="distress chunks",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        )
        consec_sub.pack()

    def _create_log_panel(self):
        """Create the scrollable detection event log."""
        log_frame = ctk.CTkFrame(self, corner_radius=12)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Log header with clear button
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        log_title = ctk.CTkLabel(
            log_header,
            text="📋  Detection Log",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_title.pack(side="left")

        clear_btn = ctk.CTkButton(
            log_header,
            text="Clear",
            font=ctk.CTkFont(size=11),
            width=60,
            height=28,
            corner_radius=6,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._clear_log
        )
        clear_btn.pack(side="right")

        # Scrollable log text area
        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            wrap="word",
            state="disabled"
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Initial log message
        self._log("ASAAP initialized. Click 'Start Monitoring' to begin.")

    def _create_footer(self):
        """Create the footer with version and privacy info."""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        footer_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        footer_left = ctk.CTkLabel(
            footer_frame,
            text="🔒 Privacy-First: Audio is processed in memory only — never saved to disk",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        )
        footer_left.pack(side="left")

        footer_right = ctk.CTkLabel(
            footer_frame,
            text="ASAAP v1.0 MVP",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60")
        )
        footer_right.pack(side="right")

    # ============================================================
    # MONITORING LOGIC
    # ============================================================

    def _start_monitoring(self):
        """Start the audio capture and inference loop."""
        if self._monitoring:
            return

        self._monitoring = True
        self.detector.reset()

        # Update UI
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._update_status("Monitoring...", "listening")

        self._log("🎤 Monitoring started — listening for distress sounds...")

        # Start audio capture
        try:
            self.audio_stream.start()
        except Exception as e:
            self._log(f"❌ Microphone error: {e}")
            self._stop_monitoring()
            return

        # Start inference thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self._monitor_thread.start()

    def _stop_monitoring(self):
        """Stop the audio capture and inference loop."""
        self._monitoring = False

        # Stop audio stream
        self.audio_stream.stop()
        self.alert_system.stop_alarm()

        # Update UI
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._update_status("Idle — Ready to monitor", "idle")
        self._update_confidence(0.0, 0)

        self._log("🛑 Monitoring stopped")

    def _monitoring_loop(self):
        """
        Background thread: captures audio chunks and runs inference.
        Updates the GUI via after() calls for thread safety.
        """
        while self._monitoring:
            # Get next audio chunk (blocks up to 1 second)
            chunk = self.audio_stream.get_chunk(timeout=1.0)

            if chunk is None:
                continue  # Timeout, loop again

            if not self._monitoring:
                break

            # Run ML inference on the chunk
            label, confidence = self.detector.predict_chunk(chunk)
            distress_count = self.detector.distress_count

            # Update GUI (thread-safe)
            self.after(0, self._update_confidence, confidence, distress_count)

            # Log the prediction
            icon = "🔴" if label == "Distress" else "🟢"
            self.after(0, self._log,
                       f"{icon} {label} — confidence: {confidence:.4f} "
                       f"(consecutive: {distress_count})")

            # Check if alert should be triggered
            if self.detector.should_alert():
                self.after(0, self._trigger_alert, confidence)

            # Chunk is automatically discarded (goes out of scope)
            # Privacy: no audio data is retained

    def _trigger_alert(self, confidence: float):
        """
        Handle alert triggering — called on the GUI thread.
        """
        self._update_status("⚠️ DISTRESS DETECTED!", "alert")
        self._log("🚨 ═══════════════════════════════════════════")
        self._log(f"🚨 DISTRESS ALERT at {get_timestamp()}")
        self._log(f"🚨 Confidence: {confidence:.4f}")
        self._log("🚨 ═══════════════════════════════════════════")

        # Trigger alert system (alarm, email, GPS)
        self.alert_system.trigger_alert(confidence, callback=self._show_alert_popup)

    def _show_alert_popup(self, event: dict):
        """
        Display an alert popup window.
        
        Args:
            event: Detection event dictionary from AlertSystem
        """
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("🚨 DISTRESS ALERT")
        popup.geometry("500x400")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)

        # Make it grab focus
        popup.grab_set()
        popup.focus_force()

        # Alert content
        alert_frame = ctk.CTkFrame(popup, corner_radius=0,
                                     fg_color=("#fef2f2", "#450a0a"))
        alert_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Warning icon
        icon_label = ctk.CTkLabel(
            alert_frame,
            text="⚠️",
            font=ctk.CTkFont(size=64)
        )
        icon_label.pack(pady=(30, 10))

        # Alert title
        title_label = ctk.CTkLabel(
            alert_frame,
            text="DISTRESS DETECTED",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#dc2626", "#ef4444")
        )
        title_label.pack(pady=(0, 15))

        # Alert details
        details_frame = ctk.CTkFrame(alert_frame, fg_color=("white", "#1a0000"),
                                      corner_radius=10)
        details_frame.pack(padx=30, pady=5, fill="x")

        details = [
            ("🕐 Time:", event['timestamp']),
            ("📊 Confidence:", f"{event['confidence']:.2%}"),
            ("📍 Location:", f"{event['gps_lat']:.6f}, {event['gps_lon']:.6f}"),
            ("📧 Alert:", "Emergency notification sent"),
        ]

        for label_text, value_text in details:
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)

            ctk.CTkLabel(
                row, text=label_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w", width=120
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=value_text,
                font=ctk.CTkFont(size=13),
                anchor="w"
            ).pack(side="left", padx=(5, 0))

        # Dismiss button
        dismiss_btn = ctk.CTkButton(
            alert_frame,
            text="Dismiss Alert",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#dc2626", "#ef4444"),
            hover_color=("#b91c1c", "#dc2626"),
            height=40,
            width=180,
            corner_radius=10,
            command=lambda: self._dismiss_alert(popup)
        )
        dismiss_btn.pack(pady=(20, 20))

    def _dismiss_alert(self, popup):
        """Dismiss the alert popup and stop alarm."""
        self.alert_system.stop_alarm()
        self.detector._alert_triggered = False
        self.detector.distress_count = 0
        popup.grab_release()
        popup.destroy()
        self._update_status("Monitoring...", "listening")
        self._log("✅ Alert dismissed — continuing monitoring")

    # ============================================================
    # GUI UPDATE HELPERS
    # ============================================================

    def _update_status(self, text: str, mode: str):
        """
        Update the status display.
        
        Args:
            text: Status text to display
            mode: "idle", "listening", or "alert"
        """
        self.status_label.configure(text=text)

        if mode == "idle":
            color = ("gray50", "gray50")
        elif mode == "listening":
            color = ("#22c55e", "#4ade80")
        elif mode == "alert":
            color = ("#ef4444", "#f87171")
        else:
            color = ("gray50", "gray50")

        self.status_label.configure(text_color=color)
        self._status_mode = mode

    def _update_confidence(self, confidence: float, distress_count: int):
        """
        Update the confidence meter and consecutive count display.
        
        Args:
            confidence: Prediction confidence (0-1)
            distress_count: Number of consecutive distress detections
        """
        # Update confidence label
        self.confidence_label.configure(text=f"{confidence:.2f}")

        # Update progress bar
        self.confidence_bar.set(min(confidence, 1.0))

        # Color based on confidence level
        if confidence > 0.8:
            color = ("#ef4444", "#f87171")  # Red — distress
        elif confidence > 0.5:
            color = ("#f59e0b", "#fbbf24")  # Amber — uncertain
        else:
            color = ("#22c55e", "#4ade80")  # Green — normal

        self.confidence_label.configure(text_color=color)
        self.confidence_bar.configure(progress_color=color)

        # Update consecutive count
        self.consecutive_label.configure(text=str(distress_count))
        if distress_count > 0:
            self.consecutive_label.configure(
                text_color=("#ef4444", "#f87171")
            )
        else:
            self.consecutive_label.configure(
                text_color=("gray50", "gray50")
            )

    def _update_pulse(self):
        """
        Animate the status dot (pulsing effect).
        Called periodically via after().
        """
        if hasattr(self, '_status_mode'):
            mode = self._status_mode
        else:
            mode = "idle"

        self._pulse_state = not self._pulse_state

        if mode == "idle":
            self.status_dot.configure(text_color=("gray50", "gray50"))
        elif mode == "listening":
            if self._pulse_state:
                self.status_dot.configure(text_color=("#22c55e", "#4ade80"))
            else:
                self.status_dot.configure(text_color=("#16a34a", "#166534"))
        elif mode == "alert":
            if self._pulse_state:
                self.status_dot.configure(text_color=("#ef4444", "#f87171"))
            else:
                self.status_dot.configure(text_color=("#b91c1c", "#7f1d1d"))

        # Schedule next pulse (500ms interval)
        self.after(500, self._update_pulse)

    def _log(self, message: str):
        """
        Add a timestamped message to the detection log.
        
        Args:
            message: Log message text
        """
        timestamp = get_timestamp()
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")  # Auto-scroll to bottom
        self.log_textbox.configure(state="disabled")

    def _clear_log(self):
        """Clear all entries from the detection log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self._log("Log cleared")

    def _on_sensitivity_change(self, value):
        """
        Handle sensitivity slider changes.
        Updates the detection threshold in real-time.
        
        Args:
            value: New threshold value from slider (0.5 to 0.95)
        """
        self.sensitivity_value_label.configure(text=f"{value:.2f}")
        self.detector.update_threshold(value)
        self._log(f"⚙️ Sensitivity threshold updated to {value:.2f}")

    def _on_close(self):
        """Handle window close — stop monitoring and exit cleanly."""
        if self._monitoring:
            self._stop_monitoring()
        self.destroy()
        logger.info("Application closed")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    """Launch the ASAAP application."""
    print("=" * 55)
    print("  ASAAP - Anti Sexual Abuse Alerting Program")
    print("  AI-Powered Passive Distress Detection System")
    print("=" * 55)

    app = ASAAPApp()
    app.mainloop()


if __name__ == "__main__":
    main()
