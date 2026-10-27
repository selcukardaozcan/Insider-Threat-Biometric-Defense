"""
Autonomous Cyber Defense Gymnasium Environment
Models the decision-making process for an active SSH session under insider threat monitoring.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np


class DefenseEnv(gym.Env):
    """
    Observation Space:
    - [0]: current_risk_score (0.0 to 1.0)
    - [1]: exponential_moving_avg_risk (0.0 to 1.0)
    - [2]: consecutive_anomalies_count (normalized 0.0 to 1.0)
    - [3]: session_duration_progress (0.0 to 1.0)

    Action Space:
    0: ALLOW
    1: AUDIT_INCREASE
    2: RATE_LIMIT
    3: TERMINATE_SESSION
    4: ISOLATE_IP
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super(DefenseEnv, self).__init__()

        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )

        self.action_space = spaces.Discrete(5)

        self.current_step = 0
        self.max_steps = 100
        self.is_true_attacker = False
        self.state = np.zeros(4, dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        # 30% chance this episode represents an insider threat / attacker
        self.is_true_attacker = np.random.rand() < 0.30

        initial_risk = np.random.uniform(0.6, 0.95) if self.is_true_attacker else np.random.uniform(0.05, 0.35)
        self.state = np.array([initial_risk, initial_risk, 1.0 if initial_risk > 0.7 else 0.0, 0.0], dtype=np.float32)
        return self.state, {}

    def step(self, action: int):
        self.current_step += 1
        reward = 0.0
        terminated = False

        risk = self.state[0]

        # Reward Calculation Matrix
        if self.is_true_attacker:
            if action in [3, 4]:  # Terminate or Isolate
                reward = 50.0   # Successfully neutralized threat
                terminated = True
            elif action in [1, 2]:
                reward = 5.0    # Cautious intermediate steps
            else:  # ALLOW
                reward = -20.0  # Missed detection penalty
        else:
            # Legitimate user
            if action in [3, 4]:
                reward = -80.0  # Heavy false-positive penalty (user disruption)
                terminated = True
            elif action in [1, 2]:
                reward = -5.0   # Slight nuisance penalty
            else:  # ALLOW
                reward = 2.0    # Correct non-interference bonus

        # Next simulated state
        noise = np.random.normal(0, 0.05)
        new_risk = np.clip((0.85 if self.is_true_attacker else 0.15) + noise, 0.0, 1.0)
        ema_risk = 0.7 * self.state[1] + 0.3 * new_risk
        consec = np.clip(self.state[2] + (0.2 if new_risk > 0.7 else -0.2), 0.0, 1.0)
        progress = float(self.current_step) / self.max_steps

        self.state = np.array([new_risk, ema_risk, consec, progress], dtype=np.float32)

        if self.current_step >= self.max_steps:
            terminated = True

        return self.state, reward, terminated, False, {"is_true_attacker": self.is_true_attacker}
