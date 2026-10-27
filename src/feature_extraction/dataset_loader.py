"""
Dataset Loader for Keystroke Dynamics Benchmarks
Supports:
1. CMU Keystroke Dynamics Benchmark Dataset (51 subjects)
2. Synthetic Continuous Typing Generator
"""

import os
import urllib.request
import pandas as pd
import numpy as np
import torch
from torch.utils.data import TensorDataset

CMU_DATASET_URL = "https://raw.githubusercontent.com/jxzhang/keystroke-dynamics/master/DSL-StrongPasswordData.csv"
DATA_DIR = "data"


def download_cmu_dataset() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, "DSL-StrongPasswordData.csv")
    if not os.path.exists(csv_path):
        print(f"[*] Downloading CMU Keystroke Dynamics Dataset from {CMU_DATASET_URL}...")
        try:
            urllib.request.urlretrieve(CMU_DATASET_URL, csv_path)
            print(f"[+] Download complete: {csv_path}")
        except Exception as e:
            print(f"[-] Could not download dataset: {e}")
            return ""
    return csv_path


def load_cmu_dataset(target_subject: str = "s002", window_size: int = 30):
    """
    Loads CMU dataset:
    - target_subject: Designated authorized user (Class 0)
    - other subjects: Impostors / Insider threats (Class 1)
    """
    csv_path = download_cmu_dataset()
    if not csv_path or not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)

    # Features are timing columns (Hold times 'H.*' and Inter-key times 'DD.*')
    feature_cols = [c for c in df.columns if c not in ["subject", "sessionIndex", "rep"]]

    X_list = []
    y_list = []

    for subject, group in df.groupby("subject"):
        timing_matrix = group[feature_cols].values  # shape: (reps, num_features)
        is_target = (subject == target_subject)

        for row in timing_matrix:
            # Reshape into sequence chunks of 4 features (Hold, Inter-key, Speed, Pause)
            row_norm = np.clip(row / 0.5, 0.0, 5.0)  # Normalize seconds
            # Pad or slice to window_size * 4
            if len(row_norm) >= window_size * 4:
                seq = row_norm[:window_size * 4].reshape(window_size, 4)
            else:
                padded = np.pad(row_norm, (0, (window_size * 4) - len(row_norm)), mode='wrap')
                seq = padded.reshape(window_size, 4)

            X_list.append(seq)
            y_list.append([0.0 if is_target else 1.0])

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)

    # Shuffle
    idx = np.random.permutation(len(X))
    return torch.tensor(X[idx]), torch.tensor(y[idx])
