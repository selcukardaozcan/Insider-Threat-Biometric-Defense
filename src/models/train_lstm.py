"""
Training Script for PyTorch Keystroke LSTM Anomaly Detector
Supports Hybrid Training: Local CUDA (RTX 2060 EVO) & Cloud (Google Colab T4).
"""

import os
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from src.models.lstm_detector import KeystrokeLSTMDetector


def generate_synthetic_keystroke_dataset(num_samples: int = 2000, seq_len: int = 30):
    """
    Generates synthetic training dataset:
    Class 0 (Authorized user): consistent flight times around 100-140ms
    Class 1 (Attacker / Impostor): irregular, hesitant, or robotic copy-paste timings
    """
    X = []
    y = []

    for _ in range(num_samples // 2):
        # Authorized user: Gaussian distributed timings
        flight = np.random.normal(loc=120.0, scale=18.0, size=(seq_len, 1))
        dwell = np.random.normal(loc=75.0, scale=10.0, size=(seq_len, 1))
        velocity = np.random.normal(loc=5.0, scale=0.5, size=(seq_len, 1))
        pause = (flight > 300.0).astype(np.float32)

        feat = np.concatenate([flight / 500.0, dwell / 200.0, velocity / 10.0, pause], axis=-1)
        X.append(feat)
        y.append([0.0])

    for _ in range(num_samples // 2):
        # Anomaly / Impostor: highly varied, large bursts or high latency
        flight = np.random.exponential(scale=280.0, size=(seq_len, 1))
        dwell = np.random.exponential(scale=110.0, size=(seq_len, 1))
        velocity = np.random.normal(loc=2.2, scale=1.2, size=(seq_len, 1))
        pause = (flight > 300.0).astype(np.float32)

        feat = np.concatenate([np.clip(flight / 500.0, 0, 5), np.clip(dwell / 200.0, 0, 5), np.clip(velocity / 10.0, 0, 2), pause], axis=-1)
        X.append(feat)
        y.append([1.0])

    indices = np.random.permutation(num_samples)
    X = np.array(X, dtype=np.float32)[indices]
    y = np.array(y, dtype=np.float32)[indices]
    return torch.tensor(X), torch.tensor(y)


def train(epochs: int = 15, batch_size: int = 32, lr: float = 0.001,
          dataset_type: str = "synthetic", save_path: str = "checkpoints/lstm_anomaly_model.pt"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Training Keystroke LSTM Model on Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if dataset_type == "cmu":
        from src.feature_extraction.dataset_loader import load_cmu_dataset
        data = load_cmu_dataset()
        if data is not None:
            X, y = data
            print(f"[+] Loaded CMU Keystroke Dynamics Dataset: {len(X)} samples.")
        else:
            print("[!] CMU Dataset could not be loaded, falling back to synthetic generator.")
            X, y = generate_synthetic_keystroke_dataset()
    else:
        X, y = generate_synthetic_keystroke_dataset()

    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)


    model = KeystrokeLSTMDetector().to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        if epoch % 3 == 0 or epoch == epochs:
            print(f"Epoch [{epoch}/{epochs}] - Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), save_path)
    print(f"[+] Model saved successfully to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--dataset", type=str, default="synthetic", choices=["synthetic", "cmu"])
    parser.add_argument("--save", type=str, default="checkpoints/lstm_anomaly_model.pt")
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, dataset_type=args.dataset, save_path=args.save)

