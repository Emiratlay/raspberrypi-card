# 🪪 Raspberry Pi Card Access System

Bu proje, **Raspberry Pi 3B+** kullanılarak **Wiegand tabanlı S6005BD proximity kart okuyucu** ile geliştirilen bir **kartlı geçiş sistemi**dir.
Sistem, SQLite veritabanı üzerinde yetkili kartları saklar ve kartların giriş/çıkış sürelerini yönetir.

---

## 📦 Kullanılan Harici Kütüphaneler

### 🔹 `pigpio`

Raspberry Pi GPIO pinlerini hassas zamanlamayla kontrol etmek için kullanılır.
[Resmî site](https://abyz.me.uk/rpi/pigpio/)

**Kurulum:**

```bash
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
```

**Daemon başlatma/durdurma:**

```bash
sudo pigpiod      # başlat
sudo killall pigpiod  # durdur
```

---

### 🔹 `pywiegandpi`

Wiegand 26/34-bit protokolüyle gelen sinyalleri çözmek için kullanılır.

**Kurulum:**

```bash
pip install pywiegandpi
```

**Örnek kullanım:**
`wiegand.py` dosyasında çalışır durumda örnek kod mevcuttur.

---

## ⚙️ Donanım Bileşenleri

| Bileşen                   | Açıklama                                 |
| ------------------------- | ---------------------------------------- |
| **S6005BD**               | Proximity kart okuyucu (Wiegand çıkışlı) |
| **Raspberry Pi 3B+**      | Ana kontrol birimi                       |
| **Dirençler (4.7k–10kΩ)** | D0 ve D1 hatları için 3.3 V pull-up      |
| **Röle / Kilit**          | Giriş kontrolü için isteğe bağlı         |

**Bağlantılar:**
Tüm bağlantı detayları `schematic.pdf` dosyasında bulunmaktadır.

---

## ⚡ Pull-up Açıklaması

S6005BD gibi okuyucular **open-collector (open-drain)** çıkış yapısına sahiptir.
Bu tip çıkışlar **yalnızca “0” sinyali üretebilir**, “1” sinyalini dışarıdan bir **pull-up direnciyle 3.3 V’a** bağlayarak biz oluştururuz.
Bu sayede Raspberry Pi GPIO pinleri sinyali doğru şekilde okuyabilir.

---

## 🧠 Çalışma Şekli

1. **Veritabanına kartlar eklenir** → `card_id` ve `duration_minutes` (dakika cinsinden).
2. Tanımsız bir kart okutulursa, **terminalde “Yetkisiz kart”** olarak bildirilir.
3. Tanımlı kart okutulursa sistem **giriş izni verir** ve kalan süreyi gösterir.
4. Süre dolmadan çıkış yapılırsa terminalde **“Süre dolmadan çıkıldı”** mesajı görüntülenir.
5. Süre dolmuşsa, terminal **“Süre bitti”** şeklinde uyarı verir.
6. (Gelecek geliştirme) Çıkışta geçen süre sistemden düşülerek güncellenecektir.

---

## 💾 Kod Dosyası

Tüm çalışma kodu `fullwiegand.py` içinde yer almaktadır.
Kod içinde 2 örnek kart 5’er dakikalık süreyle tanımlanmıştır.

---

## 📂 Dosya Yapısı

```
raspberrypi-card/
├── fullwiegand.py
├── schematic.pdf
├── wiegand.py
├── README.md
```

---
