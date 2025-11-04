#!/usr/bin/env python3
# access_control.py
#
# Gereksinimler:
#  - pigpio daemon çalışıyor (sudo pigpiod)
#  - pywiegandpi kurulu ve çalışıyor
#  - Python 3

import sqlite3
import threading
import queue
import time
from datetime import datetime, timedelta

# pywiegandpi import (callback signature = (bits, value))
from pywiegandpi import WiegandDecoder

DB_PATH = "access_control.db"

# Wiegand pinleri (BCM)
DATA0_PIN = 17
DATA1_PIN = 27

# Kuyruk: pigpio callback'inden gelen kartları buraya koyacağız
card_queue = queue.Queue()

# ---- Veritabanı yardımcı fonksiyonları ----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        card_id INTEGER PRIMARY KEY,
        duration_minutes INTEGER NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_sessions (
        card_id INTEGER PRIMARY KEY,
        start_ts TEXT NOT NULL,
        expiry_ts TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_card(card_id: int, duration_minutes: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO cards(card_id, duration_minutes) VALUES (?, ?)",
                (card_id, duration_minutes))
    conn.commit()
    conn.close()

def get_card_duration(card_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT duration_minutes FROM cards WHERE card_id = ?", (card_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_active_session(card_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT start_ts, expiry_ts FROM active_sessions WHERE card_id = ?", (card_id,))
    row = cur.fetchone()
    conn.close()
    return row  # None ya da (start_ts, expiry_ts)

def start_session(card_id: int, duration_minutes: int):
    start = datetime.utcnow()
    expiry = start + timedelta(minutes=duration_minutes)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO active_sessions(card_id, start_ts, expiry_ts) VALUES (?, ?, ?)",
                (card_id, start.isoformat(), expiry.isoformat()))
    conn.commit()
    conn.close()
    return start, expiry

def end_session(card_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM active_sessions WHERE card_id = ?", (card_id,))
    conn.commit()
    conn.close()

# ---- Kuyruk işleyicisi ----
def process_queue():
    while True:
        bits, card_value = card_queue.get()  # (bits, value) geldiğini varsayıyoruz
        try:
            process_card(bits, card_value)
        except Exception as e:
            print("İşleme hatası:", e)
        finally:
            card_queue.task_done()

def process_card(bits, card_value):
    # kart_value integer beklenir
    card_id = int(card_value)
    now = datetime.utcnow()
    duration = get_card_duration(card_id)
    if duration is None:
        print(f"[{now.isoformat()}] Yetkisiz kart: {card_id}")
        return

    active = get_active_session(card_id)
    if active is None:
        # giriş
        start, expiry = start_session(card_id, duration)
        print(f"[{now.isoformat()}] Giriş izni. Kart: {card_id} - Süre: {duration} dk - Bitiş (UTC): {expiry.isoformat()}")
    else:
        start_ts, expiry_ts = active
        expiry_dt = datetime.fromisoformat(expiry_ts)
        if now <= expiry_dt:
            # çıkış izni - süre dolmamış
            end_session(card_id)
            print(f"[{now.isoformat()}] Çıkış başarılı. Kart: {card_id} - Kalan süre var (çıkış yapıldı).")
        else:
            # süre dolmuş -> uyar
            end_session(card_id)
            print(f"[{now.isoformat()}] Süre bitti! Kart: {card_id} - expiry: {expiry_dt.isoformat()}")

# ---- pywiegandpi callback ----
def card_callback(bits, value):
    # pigpio çağrısı içinde çalışıyor, hemen kuyruğa koy
    # value bazen string veya int olabilir; kuyruğa ham gönder
    card_queue.put((bits, value))

# ---- Başlatma ----
def main():
    print("Başlatılıyor: DB init, örnek kart ekleme (varsa atla) ve kuyruk işleyiciyi başlat.")
    init_db()

    # Örnek kartlar: istersen kaldır veya düzenle
    # Kullanıcının verdiği örnekler:
    add_card(4138077, 5)   # 5 dakika
    add_card(4124178, 5)   # 5 dakika

    # Kuyruk işleyici thread
    t = threading.Thread(target=process_queue, daemon=True)
    t.start()

    # Wiegand reader başlat
    print(f"Wiegand başlatılıyor (D0={DATA0_PIN}, D1={DATA1_PIN})...")
    wg = WiegandDecoder(DATA0_PIN, DATA1_PIN, card_callback)

    print("Sistem hazır. Kart okutmayı bekliyor...")
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
    finally:
        # Temizlik
        try:
            wg.cleanup()
        except Exception:
            pass

if __name__ == "__main__":
    main()

