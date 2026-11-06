# 📋 Proje İş Paketleri ve Yol Haritası (Work Packages & Roadmap)

**Toplam Proje Süresi:** 200 Adam-Saat (%100)

| İş Paketi | Modül / Bileşen Açıklaması | Adam-Saat | Yüzdelik İş Yükü | Durum |
| :--- | :--- | :---: | :---: | :---: |
| **WP1** | Literatür Taraması, Mimari Tasarım ve Proje Planlaması | 20 Saat | %10 | Tamamlandı |
| **WP2** | Test Ortamının Kurulumu ve Wazuh/Log Altyapısının Hazırlanması | 30 Saat | %15 | Devam Ediyor (VM & SSH Hazır, Wazuh Agent/Dashboard Yapılacak) |
| **WP3** | Davranışsal Veri Toplama, Özellik Çıkarımı (Feature Extraction) | 40 Saat | %20 | Devam Ediyor (C Hook & IPC PoC Hazır, Otomatik SSH Kancası Yapılacak) |
| **WP4** | PyTorch ile LSTM ve RL Modellerinin Geliştirilmesi ve Eğitimi | 50 Saat | %25 | Tamamlandı (CMU Benchmark 20.400 Örnekle LSTM Eğitildi, SB3 PPO Entegre) |
| **WP5** | C/Python ile Otonom Müdahale Modülünün Sisteme Entegrasyonu | 30 Saat | %15 | Devam Ediyor (SIGKILL Test Edildi, iptables/eBPF Derinleştirilecek) |
| **WP6** | Performans Testleri, Optimizasyon ve Bitirme Tezi Raporlama | 30 Saat | %15 | Planlandı (ROC/AUC, FPR Analizi ve Raporlama) |
| **TOPLAM** | | **200 Saat** | **%100** | **PoC İskeleti Doğrulandı (~%30)** |

---

## İş Paketi Detayları

### WP1: Literatür Taraması ve Mimari Tasarım
- Keystroke dynamics (tuş vuruş dinamiği) literatürü ve açık veri setleri (CMU Keystroke Dynamics vb.) analizi.
- Çekirdek ve kullanıcı alanı (user-space) veri toplama metotlarının karşılaştırılması (PAM vs eBPF vs Readline Hook).
- Sistem mimarisi ve bileşenler arası haberleşme sözleşmelerinin belirlenmesi.

### WP2: Test Ortamı & Wazuh SIEM
- Ubuntu 22.04 / Debian ortamlarının hazırlanması.
- Wazuh Manager & Agent entegrasyonu, özel rule (`100200-100203`) ve decoder tanımları.
- `auditd` log kuralları ve sshd denetim politikası.

### WP3: Davranışsal Veri Toplama & Özellik Çıkarımı
- Milisaniye hassasiyetli C sensörünün (`keystroke_collector.c`) POSIX timer'lar ile derlenmesi.
- Inter-keystroke time (Flight Time), Key Dwell Time ve tuş basım sıklığının kayar pencerelerle normalize edilmesi.

### WP4: PyTorch LSTM & SB3 RL Modelleri
- PyTorch tabanlı LSTM anomali tespit modelinin hibrit (RTX 2060 EVO + Colab T4) eğitimi.
- Gymnasium tabanlı `DefenseEnv` simülasyon ortamının kurulması.
- Stable-Baselines3 PPO / DQN algoritmaları ile pekiştirmeli öğrenme ajanının eğitilmesi.

### WP5: Otonom Müdahale & Sistem Entegrasyonu
- `iptables` ve `ufw` üzerinden otomatik IP karantina kuralları.
- `pkill` ve `loginctl` ile şüpheli TTY oturumlarının gerçek zamanlı sonlandırılması.
- `systemd` daemon servisi ile 7/24 kesintisiz çalışma ve CPU %5 kotasının denetlenmesi.

### WP6: Performans & Raporlama
- Uçtan uca < 500 ms SLA doğrulama testleri.
- CPU/RAM profiling ve optimizasyon.
- Tezi destekleyecek metrikler: False Positive Rate (FPR), Detection Rate, Response Latency.
