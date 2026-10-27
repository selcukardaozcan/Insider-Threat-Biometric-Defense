#!/usr/bin/env bash
# Environment setup script for Ubuntu / Debian Linux
set -e

echo "[*] Setting up Autonomous Insider Defense System..."

# Update and install system dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    gcc \
    make \
    python3 \
    python3-pip \
    python3-venv \
    iptables \
    ufw \
    auditd \
    audispd-plugins

# Prepare Python virtual environment
if [ ! -d "venv" ]; then
    echo "[*] Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Compile C sensor hook
echo "[*] Compiling C Keystroke Collector sensor..."
cd src/sensor
make
cd ../..

# Setup system log directories
sudo mkdir -p /var/log/insider_defense
sudo chmod 755 /var/log/insider_defense

echo "[+] Setup completed successfully!"
echo "[+] To run the autonomous daemon: source venv/bin/activate && python3 -m src.defense.orchestrator"
