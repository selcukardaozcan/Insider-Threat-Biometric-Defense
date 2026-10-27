"""
Wazuh SIEM Security Event Logger
Formats decisions and telemetry into structured JSON compliant with Wazuh decoders.
"""

import json
import os
import socket
import time
from typing import Dict, Any


class WazuhLogger:
    def __init__(self, log_file: str = "/var/log/insider_defense/alerts.json", socket_path: str = "/var/ossec/queue/sockets/queue"):
        self.log_file = log_file
        self.socket_path = socket_path

        # Ensure directory exists if possible
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        except OSError:
            # Fallback to local logs directory if root permission not present
            self.log_file = "logs/alerts.json"
            os.makedirs("logs", exist_ok=True)

    def log_event(self, event_type: str, user: str, session_id: str, src_ip: str,
                  risk_score: float, action_taken: str, latency_ms: float, extra: Dict[str, Any] = None):
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "component": "insider_defense",
            "event_type": event_type,
            "user": user,
            "session_id": session_id,
            "src_ip": src_ip,
            "risk_score": round(risk_score, 4),
            "action_taken": action_taken,
            "latency_ms": round(latency_ms, 2),
            "extra": extra or {}
        }

        # Write to JSON log file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            print(f"[-] Failed to write alert to file: {e}")

        # Send to Wazuh socket if available
        if hasattr(socket, "AF_UNIX") and os.path.exists(self.socket_path):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
                    sock.sendto(json.dumps(payload).encode("utf-8"), self.socket_path)
            except Exception:
                pass

        print(f"[Wazuh ALERT] [{action_taken}] user={user} ip={src_ip} risk={risk_score:.2f} latency={latency_ms:.1f}ms")
