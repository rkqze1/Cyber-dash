# 🖥️ CYBER-DASH v2.5

**Multi-Language Terminal UI Dashboard** - Sistem monitorü, kripto fiyatları, günlük hedefler ve pomodoro zamanlayıcısı.

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Gereksinimler](#-gereksinimler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Komutlar](#-komutlar)
- [Temalar](#-temalar)
- [Yapı](#-yapı)
- [Utils Kütüphanesi](#-utils-kütüphanesi)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Özellikler

### 1. **Sistem Durumu** 🖥️
- Real-time CPU kullanımı
- RAM kullanımı (dinamik)
- Disk kullanımı (/dev)
- Saniyede bir güncelleme
- Android cihazlarda "Kısıtlı" modu

### 2. **Canlı Piyasa & Kripto** 📈
- Döviz oranları (USD/TRY, EUR/TRY, GBP/TRY)
- Kripto fiyatları (Binance API)
- **Akıllı Cache**: 1 saat TTL ile veri önbellekleme
- Otomatik 60 saniye güncelleme
- **Retry Mekanizması**: Bağlantı hatası durumunda otomatik tekrar deneme

### 3. **Günlük Hedefler** 📝
- Hedef ekleme/silme/temizleme
- JSON dosyasında kalıcı depolama (UTF-8)
- Otomatik numaralandırma
- Hedef yönetimi komutları

### 4. **Pomodoro Zamanlayıcı** ⏱️
- Özelleştirilebilir (1-99 dakika)
- Hızlı durdurma seçeneği
- Görsel sayaç (MM:SS formatında)
- Süre bittiğinde sistem zili çalma

### 5. **Hava Durumu** 🌍
- Open-Meteo API entegrasyonu (ücretsiz)
- Gerçek zamanlı sıcaklık
- Hava durumu ikonları (☀️ 🌤️ 🌧️ 🌫️)
- Şehir adı otomatik doğrulaması

### 6. **Çok Dil Desteği** 🌐
- **Türkçe (TR)** - Varsayılan
- **İngilizce (EN)**
- Dinamik dil değiştirme (yeniden başlatma yok)

### 7. **Tema Seçenekleri** 🎨
- GitHub Dark (Varsayılan)
- Dracula
- Nord
- Cyberpunk

---

## 🔧 Gereksinimler

### Python Versiyonu
- Python 3.8+

### Kütüphaneler
```bash
pip install textual psutil requests
```

**Detay:**
- `textual` >=0.20.0 - Modern TUI framework
- `psutil` >=5.9.0 - Sistem bilgisi (CPU, RAM, Disk)
- `requests` >=2.25.0 - HTTP istekleri (opsiyonel, urllib kullanılır)

### İşletim Sistemleri
✅ Linux / macOS / Windows  
✅ Android (Pydroid3, Termux)  
⚠️ İlk çalıştırmada internet bağlantısı gerekli (API veri çekişi için)

---

## 📦 Kurulum

### 1. **Dosyaları İndir**
```bash
# İki dosya aynı dizinde olmalı
cyber_dash.py
utils.py
```

### 2. **Bağımlılıkları Yükle**
```bash
pip install textual psutil requests
```

### 3. **Çalıştır**
```bash
python cyber_dash.py
```

### Pydroid3 (Android)
```bash
# Terminal aç
python cyber_dash.py
```

> **Not:** Pydroid3'te `requests` yerine yerleşik `urllib` kullanılır.

---

## 🎮 Kullanım

### Temel Başlatma
```bash
python cyber_dash.py
```

### İlk Açılış
1. Terminal açılır
2. Sistem bilgileri yüklenir
3. Kripto fiyatları çekiliyor (⏳ biraz bekleyebilir)
4. Komut giriş satırı hazır

---

## ⌨️ Komutlar

### Dil Değiştirme
```bash
!lang tr    # Türkçeye geç
!lang en    # İngilizce'ye geç
```

### Günlük Hedefler
```bash
!add-daily Spor yap        # Hedef ekle
!add-daily Kitap oku 30 dk # Çoklu kelime desteklenir

!del-daily 1               # 1. hedefi sil
!del-daily 3               # 3. hedefi sil

!clear-daily               # Tüm hedefleri temizle
```

### Hava Durumu
```bash
!weather Istanbul          # Şehir adını gir (boşluk desteklenir)
!weather London
!weather New York          # Çoklu kelime OK
```

### Kripto Fiyatları
```bash
!crypto BTC                # Bitcoin
!crypto ETH                # Ethereum
!crypto DOGE               # Dogecoin
!crypto ADA                # Cardano
```

> **Not:** Binance destekleyen tüm coin'ler çalışır (`XXX/USDT` formatında)

### Pomodoro Zamanlayıcı
```bash
!pomo 25                   # 25 dakikalık pomodoro
!pomo 5                    # 5 dakikalık mola
!pomo 1                    # 1 dakika test

!pomo stop                 # Aktif pomodoro'yu durdur
```

### Tema Değiştirme
```bash
!theme dracula             # Dracula teması
!theme nord                # Nord teması
!theme cyberpunk           # Cyberpunk teması
```

---

## 🎨 Temalar

| Tema | Renk Şeması | Best For |
|------|------------|----------|
| **GitHub Dark** (Varsayılan) | Yeşil/Gri | Minimal, GitHub hissi |
| **Dracula** | Mor/Pembe | Göz dostu, modern |
| **Nord** | Mavi/Krem | Şirin, soğuk tonlar |
| **Cyberpunk** | Neon pembe/Cyan | Futuristik, canlı |

### Tema Kulllanımı
```bash
!theme dracula    # Anında değişir, ayar kaydedilmez
```

---

## 📁 Yapı

```
├── cyber_dash.py          # Ana uygulama
├── utils.py               # Utility kütüphanesi
├── goals.json             # Hedefler (auto-created)
├── cache.db               # API cache (auto-created, SQLite)
└── README.md              # Bu dosya
```

### Dosya Açıklamaları

**cyber_dash.py**
- Textual tabanlı TUI uygulaması
- 5 widget: SystemMonitor, Market, Todo, Info
- Komut işleme ve tema yönetimi
- Lokalizasyon desteği

**utils.py**
- Dosya işlemleri (`read_json`, `save_json`)
- Network işlemleri (`fetch`, `retry`)
- Cache yönetimi (SQLite)
- Logging ve renkli output
- Sistem yardımcı fonksiyonları

**goals.json** (otomatik oluşturulur)
```json
[
  "Spor yap",
  "Kitap oku 30 dk",
  "Projede çalış"
]
```

**cache.db** (otomatik oluşturulur)
- Döviz oranları (TTL: 3600s)
- Kripto fiyatları (TTL: 3600s)
- Otomatik temizleme (expired veriler)

---

## 🛠️ Utils Kütüphanesi

`utils.py` cyber_dash'e sağladığı ana fonksiyonlar:

### Dosya İşlemleri
```python
from utils import read_json, save_json

# JSON dosya okuma (fallback desteklenir)
goals = read_json("goals.json", fallback=[])

# JSON dosya yazma (atomik, güvenli)
save_json("goals.json", goals, format_json=True)
```

### Network (Retry ile)
```python
from utils import fetch, retry

# Basit fetch
data = fetch("https://api.example.com/data", timeout=5)

# Decorator ile otomatik retry
@retry(attempts=3, delay=2, backoff=True)
def fetch_data():
    return fetch(url)
```

### Cache (SQLite)
```python
from utils import cache_set, cache_get

# Cache'e kaydet (1 saat TTL)
cache_set("market_rates", data, ttl=3600)

# Cache'den oku
cached = cache_get("market_rates")
```

### Logging
```python
from utils import log_ok, log_err, log_warn, log_info

log_ok("Başarılı işlem")
log_err("Hata meydana geldi")
log_warn("Uyarı mesajı")
log_info("Bilgi mesajı")
```

---

## 🔍 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'textual'"
**Çözüm:**
```bash
pip install textual
```

### Problem: "Network hatası - API'den veri çekilemiyor"
**Çözüm:**
1. İnternet bağlantısını kontrol et
2. Güvenlik duvarı/VPN engeli kontrol et
3. API limit'ine ulaşıldı mı kontrol et (rate limit)

**Retry mekanizması:** 3 deneme + 2-4 saniye bekleme ile otomatik

### Problem: "Android'de psutil çalışmıyor"
**Çözüm:**
- Pydroid3'te `psutil` tarafından kısıtlanabilir
- CPU/RAM "Kısıtlı (Android)" gösterecektir
- Diğer özellikler normal çalışır

### Problem: "Goals.json kaydedilmiyor"
**Çözüm:**
1. Dizin yazma izni kontrol et
2. Disk alanını kontrol et
3. UTF-8 encoding'i kontrol et

### Problem: "Tema değişmiyor"
**Çözüm:**
- Geçerli tema adı giriniz: `dracula`, `nord`, `cyberpunk`
- Yazım hatası kontrol et (küçük harf)

### Problem: "Cache verileri güncellemiyor"
**Çözüm:**
- Cache.db dosyasını silin (otomatik yeniden oluşturulur)
- TTL süresi 3600 saniyedir (1 saat)
- Manuel reset: `rm cache.db`

---

## 🔐 Güvenlik & İyi Pratikler

### API Limitleri
- **Frankfurter API**: Dakikada max. 180 istek (ücretsiz)
- **Binance API**: Dakikada max. 1200 istek (ücretsiz)
- **Open-Meteo API**: Sınırı yok (ücretsiz)

### Cache & Performans
- Döviz/kripto verileri 1 saat cache'lenir
- Tekrarlayan istekler cache'den okunur
- Bağlantı kesintisinde cache verileri kullanılır

### Dosya Güvenliği
- Atomik yazma (temp file → main file)
- Yazma başarısızsa orijinal dosya korunur
- UTF-8 encoding zorunlu

---

## 📊 Mimari

```
┌─────────────────────────────────────────┐
│       CyberDash (Textual App)           │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ SysMonitor   │  │ Market       │   │
│  │ (1s update)  │  │ (60s update) │   │
│  └──────────────┘  └──────────────┘   │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Todo         │  │ Info         │   │
│  │ (JSON)       │  │ (Weather+    │   │
│  │              │  │  Pomodoro)   │   │
│  └──────────────┘  └──────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │ Input (Commands)                │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↓ (uses)
┌─────────────────────────────────────────┐
│         Utils Library                    │
├─────────────────────────────────────────┤
│                                         │
│  ├─ File I/O (read_json, save_json)   │
│  ├─ Network (fetch, retry, cache)     │
│  ├─ Logging (log_ok, log_err, etc)    │
│  ├─ Security (hash, encode/decode)    │
│  └─ System (timers, signal handlers)  │
│                                         │
└─────────────────────────────────────────┘
           ↓ (accesses)
┌─────────────────────────────────────────┐
│        External Storage                  │
├─────────────────────────────────────────┤
│                                         │
│  ├─ goals.json (günlük hedefler)     │
│  └─ cache.db (döviz/kripto cache)    │
│                                         │
└─────────────────────────────────────────┘
```

---

## 💡 Kullanım Örnekleri

### Örnek 1: Günlük Rutinin Ayarla
```
1. App başla
2. !lang tr          # Türkçeye geç
3. !add-daily Spor yap
4. !add-daily Kitap oku 30 dk
5. !add-daily Proje çalış
6. !pomo 25          # 25 dakikalık çalış
7. Hava durumuna bak: !weather Istanbul
```

### Örnek 2: Kripto Takibi
```
1. !crypto BTC      # Bitcoin fiyatını gör
2. !crypto ETH      # Ethereum fiyatını gör
3. !theme cyberpunk # Tema değiştir
4. Veriler cache'lenir, sonraki istek hızlı yüklenir
```

### Örnek 3: Temaya Göre Çalış
```
Gündüz:  !theme nord
Gece:    !theme dracula
Oyun:    !theme cyberpunk
```

---

## 📝 Kütüphane Versiyonları

| Kütüphane | Version | Not |
|-----------|---------|-----|
| textual | >=0.20.0 | Terminal UI |
| psutil | >=5.9.0 | Sistem bilgisi |
| requests | >=2.25.0 | HTTP (urllib fallback) |
| Python | >=3.8 | Gerekli |

---

## 🤝 Katkılar & Feedback

Hataları veya önerileri raporla:
- Komutların çalışmadığını doğrula
- Utils.py'nin yüklü olduğunu kontrol et
- İnternet bağlantısını kontrol et
- Log çıktısını kontrol et (stderr)

---

## 📄 Lisans

Bu proje açık kaynak ve özgürce kullanılabilir.

---

## 🚀 Hızlı Başlangıç

```bash
# 1. Kurulum
pip install textual psutil requests

# 2. Çalıştır
python cyber_dash.py

# 3. Komut gir
!lang tr
!add-daily Örnek hedef
!weather Istanbul
!crypto BTC
!pomo 25
!theme dracula
```

---

**Made with ❤️ | Mert's Terminal Dashboard**

Sürüm: 2.5 | Son güncelleme: 2026

