"""
Training Script for Autonomous Defense Agent using Stable-Baselines3 (PPO)
"""

import os
import argparse
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from src.rl_agent.env import DefenseEnv


def train_rl(total_timesteps: int = 50000, save_path: str = "checkpoints/sb3_ppo_defense.zip"):
    print("[*] Initializing PPO training for autonomous cyber defense agent...")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    vec_env = make_vec_env(DefenseEnv, n_envs=4)

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1
    )

    model.learn(total_timesteps=total_timesteps)
    model.save(save_path)
    print(f"[+] RL Agent trained and saved to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=30000)
    parser.add_argument("--save", type=str, default="checkpoints/sb3_ppo_defense.zip")
    args = parser.parse_args()
    train_rl(total_timesteps=args.timesteps, save_path=args.save)
