# BioGuard: Autonomous Cyber Defense Agent 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-success.svg)]()

**BioGuard** is an open-source, Zero-Trust endpoint security agent designed to detect and autonomously mitigate insider threats and stolen credential attacks on SSH sessions. 

Traditional security relies on static passwords. BioGuard assumes that credentials can be compromised. Instead of trusting the password, it continuously authenticates the user by analyzing their **behavioral biometrics** (keystroke dynamics and command timing) using Deep Learning, and isolates anomalies in real-time using a Reinforcement Learning (RL) agent.

## 🚀 Key Features

- **Behavioral Biometrics (Keystroke Dynamics):** Captures and analyzes inter-keystroke timings and command execution speeds with millisecond precision via Linux `auditd`.
- **Deep Learning Anomaly Detection:** Utilizes PyTorch-based LSTM networks to model the legitimate root/admin user's unique typing DNA.
- **Autonomous Active Response:** Employs a Reinforcement Learning agent (Stable-Baselines3) to make real-time mitigation decisions (e.g., dropping sessions via `iptables` or eBPF) without waiting for a human SOC analyst.
- **Lightweight & Portable:** Designed to consume <5% CPU, easily deployable across Ubuntu and Debian environments.
- **Centralized SIEM Integration:** Forwards all telemetry, risk scores, and agent actions to Wazuh for centralized SOC monitoring.

## 🏗️ System Architecture

1. **Sensor Node (C / Python):** Monitors SSH TTY inputs and extracts keystroke timing vectors.
2. **AI Engine (PyTorch):** Processes the time-series data to output a real-time risk score.
3. **Mitigation Agent (RL / eBPF):** Dynamically alters host firewall rules to throttle or terminate malicious sessions based on the risk score threshold.

## 🛠️ Tech Stack

- **Machine Learning:** Python, PyTorch, Stable-Baselines3, Scikit-learn
- **System/Security:** C (eBPF), Linux `auditd`, Wazuh, `iptables`
- **Infrastructure:** VS Code Remote-SSH, Tailscale, CUDA (Nvidia RTX 2060 for local training)

## ⚙️ Getting Started

> **Note:** BioGuard is currently in active development. Detailed installation and model training instructions will be added as the core modules are released.

### Prerequisites (Planned)
- Ubuntu 22.04 LTS or Debian 11+
- Python 3.10+
- Wazuh Agent (optional but recommended)

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🎓 Academic Background

This project is initiated as a senior capstone project (Graduation Thesis) at **Bolu Abant Izzet Baysal University**, Department of Computer Engineering, under the supervision of Dr. İsmail Parlak. It aims to bridge the gap between academic research in behavioral biometrics and practical, open-source autonomous SOC engineering.

**Developer:** Selçuk Arda Özcan
