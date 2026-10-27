# 🏗️ Sistem Mimarisi (Architecture Specification)

## 1. Genel Mimari Bakış
Bu sistem, çalınmış kimlik bilgileriyle (stolen credentials) SSH oturumu açan tehdit aktörlerini, kullanıcının **davranışsal biyometrisi (keystroke dynamics)** üzerinden gerçek zamanlı tespit eden ve Takviyeli Öğrenme (RL) ile otonom olarak izole eden uç nokta savunma mimarisidir.

```
       +---------------------------------------------+
       |           SSH Client / Terminal             |
       +---------------------------------------------+
                              | (Tuş vuruşları & Zaman damgaları)
                              v
       +---------------------------------------------+
       |   C Sensör Kancası (keystroke_collector)    |
       |  clock_gettime(CLOCK_MONOTONIC) (ms hassas) |
       +---------------------------------------------+
                              | Unix Domain Socket (/var/run/insider_sensor.sock)
                              v
       +---------------------------------------------+
       |       Özellik Çıkarımı (Feature Extractor)  |
       |  - Flight Time, Dwell Time, Velocity, Pause |
       +---------------------------------------------+
                              | Kayar Pencere (Window size: 30)
                              v
       +---------------------------------------------+
       |     PyTorch LSTM Anomali Tespit Modeli      |
       |   İnferans Süresi: ~2-5 ms | Çıktı: Risk [0..1]
       +---------------------------------------------+
                              | Durum Vektörü [Risk, EMA, Anomali Serisi]
                              v
       +---------------------------------------------+
       |     RL Karar Ajanı (Stable-Baselines3 PPO)   |
       |  Aksiyonlar: ALLOW, AUDIT, TERMINATE, DROP  |
       +---------------------------------------------+
               /                              \
              v                                v
+----------------------------+   +----------------------------+
|  Otonom Müdahale Motoru    |   |  Merkezi Loglama & SIEM    |
| - pkill / SIGKILL (Oturum) |   | - Wazuh SIEM Decoders/Rules|
| - iptables/ufw (IP Düşürme)|   | - auditd kernel log entegr.|
+----------------------------+   +----------------------------+
```

---

## 2. SLA ve Performans Bütçesi (Non-Functional Requirements)

| Bileşen / Faz | Hedeflenen Maksimum Süre | Tipik Süre |
| :--- | :--- | :--- |
| C Kancası (IPC Paket iletimi) | 5 ms | < 1 ms |
| Özellik Çıkarım Tamponu | 5 ms | < 1 ms |
| PyTorch LSTM İnferansı | 30 ms | 4 ms (CPU) / 1 ms (CUDA) |
| SB3 RL Politika Kararı | 10 ms | < 2 ms |
| Ağ & Oturum Müdahalesi (iptables/pkill) | 50 ms | 12 ms |
| Wazuh JSON Log Yazımı | 20 ms | 3 ms |
| **Toplam Uçtan Uca Gecikme (SLA)** | **< 500 ms** | **~ 22 ms (Tam Başarılı)** |

### İşlemci & Kaynak Yönetimi
- **Maksimum CPU Kullanımı:** `%5` tavan limiti (`systemd CPUQuota=5%` ile garanti altına alınmıştır).
- **Bellek Ayak İzi:** `< 512 MB`.

---

## 3. Güvenlik ve Eylemler (Action Space)

1. **`0: ALLOW`** -> Normal kullanıcı paterni; müdahale yapılmaz.
2. **`1: AUDIT_INCREASE`** -> Şüphe eşiği; auditd ve Wazuh kayıt yoğunluğu artırılır.
3. **`2: RATE_LIMIT`** -> Kullanıcı terminal girdilerine yapay gecikme verilerek hareketleri yavaşlatılır.
4. **`3: TERMINATE_SESSION`** -> Oturum derhal `pkill -9` / `loginctl` ile sonlandırılır.
5. **`4: ISOLATE_IP`** -> İlgili kaynak IP adresi `iptables`/`ufw` kuralları ile tamamen düşürülür (DROP).
