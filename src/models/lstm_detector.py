"""
PyTorch LSTM Behavioral Biometrics Anomaly Detector
Detects unauthorized user behavior by learning authorized user keystroke dynamics.
Provides millisecond-latency inference (<500ms SLA).
"""

import torch
import torch.nn as nn
import numpy as np


class KeystrokeLSTMDetector(nn.Module):
    def __init__(self, input_dim: int = 4, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(KeystrokeLSTMDetector, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Bidirectional or standard LSTM encoder
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Classification / Anomaly Head
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Outputs anomaly risk score [0.0 - 1.0]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: (batch_size, sequence_length, input_dim)
        Output: (batch_size, 1) risk score
        """
        lstm_out, (hn, _) = self.lstm(x)
        # Use last hidden state
        last_hidden = hn[-1]
        risk_score = self.fc(last_hidden)
        return risk_score

    def predict_risk(self, feature_matrix: np.ndarray, device: str = "cpu") -> float:
        """
        Single sample inference for real-time scoring.
        """
        self.eval()
        with torch.no_grad():
            tensor_x = torch.from_numpy(feature_matrix).unsqueeze(0).to(device)
            score = self.forward(tensor_x).item()
            return float(score)
