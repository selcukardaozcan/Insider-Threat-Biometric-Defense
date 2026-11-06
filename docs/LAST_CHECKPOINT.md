# 📌 Proje Durum Özeti ve Kaldığımız Yer (Checkpoint - 6 Kasım 2026)

## 🎯 Tamamlanan Kritik Başarılar:
1. **CMU Gerçek Veri Seti Eğitimi (WP4):**
   - CMU Keystroke Benchmark (20.400 gerçek biyometrik örnek, 51 kullanıcı) başarıyla indirildi ve PyTorch LSTM modeli eğitilip `checkpoints/lstm_anomaly_model.pt` olarak güncellendi.
2. **Otomatik ve Görünmez SSH Kancası (WP3):**
   - `/etc/profile.d/insider_defense_hook.sh` ile sensör sisteme entegre edildi. Kullanıcı veya saldırgan SSH ile bağlandığı an sensör arka planda tamamen sessiz ve şeffaf olarak başlıyor.
3. **İnsan Doğasına Uygun Anomali Toleransı:**
   - Düşünme/okuma molaları (`flight > 2000ms`) normalize edildi. Tek bir duraklamada oturum kapatılması engellendi.
   - `TERMINATE_SESSION` kararı için üst üste en az 3-4 anomali vuruşu (streak >= 3) şartı bağlandı.

---

## ⏸️ Bir Sonraki Oturumda Kaldığımız Yer:

### 1. Test Adımı:
- Ubuntu'da: `git pull origin main && sudo venv/bin/python3 -m src.defense.orchestrator`
- Windows'tan SSH ile bağlanıp hem "insan gibi duraklamalı yazım" hem de "ısrarlı saldırgan yazımı" testi doğrulanacak.

### 2. Kalan Teknik Madde (Madde 3):
- **Wazuh SIEM Canlı Entegrasyonu:** `/var/log/insider_defense/alerts.json` loglarının Wazuh kurallarıyla (`wazuh_rule_sample.xml`) tam uyumunun teyidi.

### 3. Hoca'nın 2. Ödevi (Arayüz Tasarımı & PDF):
- Son teslim tarihi: **26 Kasım Perşembe 23:59**.
- Koyu temalı kurumsal SOC Dashboard ekran tasarımları ve akademik açıklamalarından oluşan PDF hazırlanacak.
