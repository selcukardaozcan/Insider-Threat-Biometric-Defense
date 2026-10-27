"""
RL Defense Agent Wrapper
Loads trained Stable-Baselines3 policy or falls back to safety heuristic policy.
"""

import os
from typing import Optional
import numpy as np

ACTION_NAMES = {
    0: "ALLOW",
    1: "AUDIT_INCREASE",
    2: "RATE_LIMIT",
    3: "TERMINATE_SESSION",
    4: "ISOLATE_IP"
}

class DefenseAgent:
    def __init__(self, checkpoint_path: Optional[str] = None):
        self.checkpoint_path = checkpoint_path
        self.model = None

        if checkpoint_path and os.path.exists(checkpoint_path):
            try:
                from stable_baselines3 import PPO
                self.model = PPO.load(checkpoint_path)
                print(f"[+] Loaded SB3 RL Agent policy from {checkpoint_path}")
            except Exception as e:
                print(f"[!] Warning: Could not load SB3 model ({e}), falling back to heuristic policy.")

    def decide_action(self, observation: np.ndarray) -> (int, str):
        """
        observation: [current_risk, ema_risk, consecutive_anomalies, progress]
        Returns: (action_id, action_name)
        """
        if self.model is not None:
            action, _ = self.model.predict(observation, deterministic=True)
            action_id = int(action)
        else:
            # High-assurance safety heuristic policy
            risk = observation[0]
            consec = observation[2]

            if risk > 0.88 and consec >= 0.6:
                action_id = 4  # ISOLATE_IP
            elif risk > 0.75:
                action_id = 3  # TERMINATE_SESSION
            elif risk > 0.50:
                action_id = 1  # AUDIT_INCREASE
            else:
                action_id = 0  # ALLOW

        return action_id, ACTION_NAMES.get(action_id, "ALLOW")
