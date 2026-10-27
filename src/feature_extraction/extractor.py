"""
Feature Extraction Engine
Transforms millisecond-level keystroke events into temporal feature vectors
for the LSTM anomaly detection model.
"""

from collections import deque
from typing import Dict, List, Optional
import numpy as np


class SessionBuffer:
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.flight_times = deque(maxlen=window_size)
        self.dwell_times = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)

    def append(self, flight_time_ms: float, dwell_time_ms: float = 80.0, timestamp_ms: float = 0.0):
        self.flight_times.append(flight_time_ms)
        self.dwell_times.append(dwell_time_ms)
        self.timestamps.append(timestamp_ms)

    def is_ready(self) -> bool:
        return len(self.flight_times) >= self.window_size

    def extract_features(self) -> Optional[np.ndarray]:
        """
        Extracts temporal feature matrix (window_size, 4):
        - flight_time (normalized)
        - dwell_time (normalized)
        - typing_velocity (keys per second)
        - pause_indicator (1.0 if flight_time > 300ms else 0.0)
        """
        if not self.is_ready():
            return None

        flight_arr = np.array(self.flight_times, dtype=np.float32)
        dwell_arr = np.array(self.dwell_times, dtype=np.float32)

        # Typing velocity calculation (window duration in seconds)
        if len(self.timestamps) > 1 and (self.timestamps[-1] - self.timestamps[0]) > 0:
            total_duration_sec = (self.timestamps[-1] - self.timestamps[0]) / 1000.0
            velocity = len(self.timestamps) / total_duration_sec
        else:
            velocity = 4.5  # Typical human baseline

        # Pauses > 300ms
        pause_flags = (flight_arr > 300.0).astype(np.float32)

        # Normalization (cap values to prevent outliers)
        norm_flight = np.clip(flight_arr / 500.0, 0.0, 5.0)
        norm_dwell = np.clip(dwell_arr / 200.0, 0.0, 5.0)
        norm_velocity = np.full_like(norm_flight, np.clip(velocity / 10.0, 0.0, 2.0))

        features = np.stack([norm_flight, norm_dwell, norm_velocity, pause_flags], axis=-1)
        return features


class FeatureExtractor:
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.sessions: Dict[str, SessionBuffer] = {}

    def process_event(self, event: dict) -> Optional[np.ndarray]:
        session_id = event.get("session_id", "default")
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionBuffer(window_size=self.window_size)

        buffer = self.sessions[session_id]
        flight_time = float(event.get("flight_time_ms", 120.0))
        dwell_time = float(event.get("dwell_ms", 75.0))
        timestamp = float(event.get("timestamp_ms", 0.0))

        buffer.append(flight_time, dwell_time, timestamp)
        return buffer.extract_features()

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
