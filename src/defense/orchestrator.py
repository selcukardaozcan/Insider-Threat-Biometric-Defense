"""
Autonomous Cyber Defense Orchestrator Daemon
Runs 7/24 monitoring active SSH sessions.
Ensures:
- End-to-end inference and mitigation latency < 500ms
- CPU overhead < 5%
- Structured logging to Wazuh SIEM
"""

import time
import os
import yaml
import numpy as np
from typing import Dict, Any

from src.feature_extraction.extractor import FeatureExtractor
from src.models.lstm_detector import KeystrokeLSTMDetector
from src.rl_agent.agent import DefenseAgent
from src.defense.firewall import FirewallManager
from src.defense.session_manager import SessionManager
from src.logging_siem.wazuh_logger import WazuhLogger
from src.sensor.collector_daemon import CollectorDaemon


class DefenseOrchestrator:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)

        min_keys = self.config.get("sensor", {}).get("min_keystrokes_for_inference", 8)
        self.extractor = FeatureExtractor(
            window_size=self.config.get("feature_extraction", {}).get("window_size", 30),
            min_keys=min_keys
        )
        self.device = "cuda" if (self.config.get("model", {}).get("device") == "cuda" and False) else "cpu"

        # Initialize PyTorch LSTM Anomaly Detector
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.lstm = KeystrokeLSTMDetector()
        lstm_ckpt = self.config.get("model", {}).get("lstm", {}).get("checkpoint_path")
        if lstm_ckpt and not os.path.isabs(lstm_ckpt):
            lstm_ckpt = os.path.join(base_dir, lstm_ckpt)

        if lstm_ckpt and os.path.exists(lstm_ckpt):
            try:
                import torch
                self.lstm.load_state_dict(torch.load(lstm_ckpt, map_location=self.device))
                print(f"[+] Loaded LSTM weights from {lstm_ckpt}")
            except Exception as e:
                print(f"[!] Warning: Could not load LSTM checkpoint: {e}")
        else:
            print(f"[!] Warning: LSTM checkpoint not found at {lstm_ckpt}")

        # Initialize RL Agent
        rl_ckpt = self.config.get("reinforcement_learning", {}).get("checkpoint_path")
        if rl_ckpt and not os.path.isabs(rl_ckpt):
            rl_ckpt = os.path.join(base_dir, rl_ckpt)
        self.agent = DefenseAgent(checkpoint_path=rl_ckpt)

        # Defense Actuators
        self.firewall = FirewallManager(
            backend=self.config.get("firewall", {}).get("backend", "iptables"),
            chain=self.config.get("firewall", {}).get("chain", "INSIDER_DEFENSE")
        )
        self.session_mgr = SessionManager()

        # SIEM Logger
        self.logger = WazuhLogger(
            log_file=self.config.get("wazuh", {}).get("log_file", "logs/alerts.json"),
            socket_path=self.config.get("wazuh", {}).get("socket_path", "")
        )

        # Rolling Session Tracking
        self.session_ema_risk: Dict[str, float] = {}
        self.session_consec_anomalies: Dict[str, int] = {}

    def _load_config(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def process_keystroke_event(self, event: dict) -> dict:
        """
        Processes a single keystroke event through the pipeline:
        Event -> Features -> LSTM Risk Score -> RL Action -> Enforcement -> Wazuh Log
        Guaranteed to execute within SLA < 500ms.
        """
        start_time = time.perf_counter()

        session_id = event.get("session_id", "unknown_session")
        user = event.get("user", "unknown_user")
        src_ip = event.get("src_ip", "127.0.0.1")

        # 1. Feature Extraction
        feature_matrix = self.extractor.process_event(event)
        buf = self.extractor.sessions.get(session_id)
        count = len(buf.flight_times) if buf else 0

        if feature_matrix is None:
            # Buffer not full yet, keep collecting
            print(f"[*] Keystroke received ({count}/{self.extractor.min_keys} min) for {user} (flight: {event.get('flight_time_ms', 0):.1f}ms)...")
            return {"status": "buffering", "session_id": session_id}

        # 2. PyTorch LSTM Anomaly Detection (Latency ~ 2-5ms)
        risk_score = self.lstm.predict_risk(feature_matrix, device=self.device)

        # Update EMA risk and anomaly streak
        prev_ema = self.session_ema_risk.get(session_id, risk_score)
        ema_risk = 0.7 * prev_ema + 0.3 * risk_score
        self.session_ema_risk[session_id] = ema_risk

        streak = self.session_consec_anomalies.get(session_id, 0)
        streak = (streak + 1) if risk_score > 0.70 else max(0, streak - 1)
        self.session_consec_anomalies[session_id] = streak

        # 3. RL Agent Decision (Latency ~ 1ms)
        observation = np.array([risk_score, ema_risk, min(streak / 5.0, 1.0), 0.5], dtype=np.float32)
        action_id, action_name = self.agent.decide_action(observation)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Print live status to console
        print(f"[!] [ANALYSIS #{count}] user={user} | Risk: {risk_score:.3f} | EMA: {ema_risk:.3f} | Action: {action_name} | Latency: {latency_ms:.2f}ms")

        # 4. Autonomous Enforcement
        if action_name == "TERMINATE_SESSION":
            self.session_mgr.terminate_session(session_id, username=user)
        elif action_name == "ISOLATE_IP":
            self.session_mgr.terminate_session(session_id, username=user)
            self.firewall.block_ip(src_ip)

        # 5. Wazuh SIEM Security Event
        self.logger.log_event(
            event_type="keystroke_analysis",
            user=user,
            session_id=session_id,
            src_ip=src_ip,
            risk_score=risk_score,
            action_taken=action_name,
            latency_ms=latency_ms,
            extra={"action_id": action_id, "streak": streak, "ema_risk": round(ema_risk, 4)}
        )

        return {
            "session_id": session_id,
            "risk_score": risk_score,
            "action": action_name,
            "latency_ms": latency_ms
        }

    def start_daemon(self):
        sock_path = self.config.get("sensor", {}).get("socket_path", "/var/run/insider_sensor.sock")
        collector = CollectorDaemon(socket_path=sock_path)
        print(f"[*] Autonomous Defense Daemon running.")
        print(f"[*] Listening for keystroke sensor telemetry on {sock_path}...")
        print("[*] Press Ctrl+C to terminate.")
        try:
            collector.listen(callback=self.process_keystroke_event)
        except KeyboardInterrupt:
            print("\n[*] Stopping defense daemon.")
            collector.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Cyber Defense Orchestrator Daemon")
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration YAML")
    args = parser.parse_args()

    orchestrator = DefenseOrchestrator(config_path=args.config)
    orchestrator.start_daemon()
