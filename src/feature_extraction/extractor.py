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

    def is_ready(self, min_keys: int = 8) -> bool:
        return len(self.flight_times) >= min_keys

    def extract_features(self, min_keys: int = 8) -> Optional[np.ndarray]:
        """
        Extracts temporal feature matrix (sequence_length, 4):
        - flight_time (normalized)
        - dwell_time (normalized)
        - typing_velocity (keys per second)
        - pause_indicator (1.0 if flight_time > 300ms else 0.0)
        """
        if not self.is_ready(min_keys=min_keys):
            return None

        flight_arr = np.array(self.flight_times, dtype=np.float32)
        # Cap single thinking pauses:
        # If flight_time > 2000ms (2 seconds), it's a natural thinking/reading pause,
        # not necessarily an anomalous typing jitter. Cap it at 1200ms for feature normalization.
        clean_flight_arr = np.where(flight_arr > 2000.0, 1200.0, flight_arr)

        # Dynamic dwell estimation if default: hesitant/irregular flight correlates with longer dwell
        dwell_arr = np.array([
            min(250.0, 75.0 + (f / 30.0)) if d == 75.0 and f > 500.0 else
            (max(35.0, 40.0 + f) if d == 75.0 and f < 50.0 else d)
            for f, d in zip(clean_flight_arr, self.dwell_times)
        ], dtype=np.float32)

        # Typing velocity calculation (window duration in seconds)
        if len(self.timestamps) > 1 and (self.timestamps[-1] - self.timestamps[0]) > 0:
            total_duration_sec = (self.timestamps[-1] - self.timestamps[0]) / 1000.0
            velocity = len(self.timestamps) / max(total_duration_sec, 0.1)
        else:
            velocity = 4.5  # Typical human baseline

        # Pauses > 300ms but exclude single long idle pauses
        pause_flags = ((flight_arr > 300.0) & (flight_arr < 5000.0)).astype(np.float32)

        # Normalization (cap values to prevent outliers)
        norm_flight = np.clip(clean_flight_arr / 500.0, 0.0, 5.0)
        norm_dwell = np.clip(dwell_arr / 200.0, 0.0, 5.0)
        norm_velocity = np.full_like(norm_flight, np.clip(velocity / 10.0, 0.0, 2.0))

        features = np.stack([norm_flight, norm_dwell, norm_velocity, pause_flags], axis=-1)

        # Pad to full window_size (30) so LSTM receives expected temporal sequence length
        if len(features) < self.window_size:
            pad_len = self.window_size - len(features)
            pad = np.tile(features[-1:], (pad_len, 1))
            features = np.vstack([features, pad])

        return features


class FeatureExtractor:
    def __init__(self, window_size: int = 30, min_keys: int = 8):
        self.window_size = window_size
        self.min_keys = min_keys
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
        return buffer.extract_features(min_keys=self.min_keys)

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
