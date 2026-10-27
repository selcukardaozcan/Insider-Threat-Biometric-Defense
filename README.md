# 🛡️ Autonomous Insider Threat Cyber Defense System
> **Çalınmış Kimlik Bilgileriyle Yapılan SSH Sızmalarını Davranışsal Biyometri ve Pekiştirmeli Öğrenme (RL) ile Engelleyen Otonom Savunma Mimarisi**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Stable-Baselines3](https://img.shields.io/badge/RL-Stable--Baselines3-green.svg)](https://github.com/DLR-RM/stable-baselines3)
[![Wazuh SIEM](https://img.shields.io/badge/SIEM-Wazuh%20Ready-00a4e4.svg)](https://wazuh.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Proje Özeti
Bu proje, sunucu sistemlerine yönelik gerçekleştirilen ve geleneksel kural tabanlı sistemler tarafından tespit edilemeyen **çalınmış kimlik bilgileriyle (insider threat)** yapılan sızmaları engellemek için tasarlanmış uç nokta otonom siber savunma mimarisidir.

Sisteme SSH üzerinden giriş yapan kullanıcının komut yazma hızı, tuşlar arasındaki gecikmeler (flight time) ve basılı tutma süreleri (dwell time) milisaniye hassasiyetinde toplanır. **PyTorch LSTM** derin öğrenme ağı bu verileri anomali skoruna dönüştürürken, **Stable-Baselines3 (PPO)** Pekiştirmeli Öğrenme ajanı insan müdahalesi beklemeden şüpheli SSH oturumunu sonlandırır ve saldırgan IP adresini güvenlik duvarı üzerinden (`iptables`/`ufw`) bloke eder.

Tüm güvenlik kararları ve metrikler merkezi **Wazuh SIEM** ve **auditd** sistemine uyumlu JSON formatında kayıt altına alınır.

---

## ⚡ Temel Özellikler ve Gereksinimler

- ⏱️ **Ultra-Düşük Gecikme:** Uçtan uca veri analizi ve müdahale süresi **< 500 ms** SLA.
- ⚙️ **Hafif ve Verimli:** Sunucu CPU kullanım tavanı **< %5** (`systemd CPUQuota=5%`).
- 🤖 **Otonom Eylem:** Kademeli savunma (Gözlem -> Log Yoğunlaştırma -> Oturum İptali -> IP İzolasyonu).
- 🧩 **Hibrit Teknoloji Yığını:**
  - **Sensör:** Düşük seviyeli C modülü (`keystroke_collector.c`).
  - **Yapay Zeka:** PyTorch LSTM zaman serisi anomali tespiti + Stable-Baselines3 PPO.
  - **SIEM:** Wazuh özel decoders & rules (`100200-100203`), Linux auditd.
  - **Platform:** Ubuntu / Debian Linux, systemd daemon servisi.

---

## 📁 Proje Dizin Yapısı

```
Insider_Deneme/
├── config/
│   ├── config.yaml                    # Sistem, model ve ağ parametreleri
│   ├── wazuh_rule_sample.xml          # Wazuh SIEM kural ve dekoder tanımları
│   └── systemd/
│       └── insider-defense.service    # 7/24 kesintisiz çalışma ve CPU %5 kotası
├── docs/
│   ├── ARCHITECTURE.md                # Ayrıntılı mimari ve gecikme bütçesi
│   └── WORK_PACKAGES.md               # 200 saatlik WP1-WP6 yol haritası
├── scripts/
│   ├── setup_env.sh                   # Ubuntu/Debian otomatik kurulum betiği
│   └── simulate_typing.py             # Sentetik tuş dinamiği simülatörü & benchmark
├── src/
│   ├── sensor/                        # C dili ile milisaniye hassas tuş kancası
│   │   ├── keystroke_collector.c
│   │   ├── Makefile
│   │   └── collector_daemon.py
│   ├── feature_extraction/            # Kayar pencere & IKD/Dwell/Velocity vektörleri
│   │   └── extractor.py
│   ├── models/                        # PyTorch LSTM Anomali Tespiti
│   │   ├── lstm_detector.py
│   │   └── train_lstm.py              # CUDA (RTX 2060 / Colab T4) destekli eğitim
│   ├── rl_agent/                      # Pekiştirmeli Öğrenme Savunma Ajanı
│   │   ├── env.py                     # Gymnasium tabanlı siber savunma ortamı
│   │   ├── agent.py                   # Karar motoru & inferans sarmalayıcısı
│   │   └── train_rl.py                # SB3 PPO eğitim betiği
│   ├── defense/                       # Otonom Müdahale Motoru
│   │   ├── firewall.py                # iptables / ufw IP karantina
│   │   ├── session_manager.py         # SSH tty oturum sonlandırma
│   │   └── orchestrator.py            # Ana orkestrasyon döngüsü
│   └── logging_siem/                  # Wazuh JSON Olay Dağıtıcısı
│       └── wazuh_logger.py
└── requirements.txt
```

---

## 🚀 Hızlı Başlangıç (Quick Start)

### 1. Ortam Kurulumu
```bash
# Depoyu klonlayın ve dizine girin
cd Insider_Deneme

# Gerekli bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 2. Simülatörü ve Test Döngüsünü Çalıştırma
Sistemi test etmek ve SLA gecikmesini (<500ms) doğrulamak için hazır simülasyonu çalıştırabilirsiniz:
```bash
python scripts/simulate_typing.py
```

### 3. Model Eğitimi (PyTorch & RL)
```bash
# PyTorch LSTM anomali modelini eğit:
python -m src.models.train_lstm --epochs 15

# Stable-Baselines3 Pekiştirmeli Öğrenme ajanını eğit:
python -m src.rl_agent.train_rl --timesteps 30000
```

### 4. Linux Üzerinde Servis Olarak Başlatma
```bash
sudo cp config/systemd/insider-defense.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now insider-defense.service
```

---

## 👥 Geliştirme ve İş Paketleri
Detaylı iş paketleri dökümantasyonu için [docs/WORK_PACKAGES.md](docs/WORK_PACKAGES.md) dosyasını inceleyebilirsiniz.
Sistem mimarisi ve SLA metrikleri için [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) dosyasını inceleyebilirsiniz.
