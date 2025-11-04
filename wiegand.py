from pywiegandpi import WiegandDecoder
import time

DATA0_PIN = 17
DATA1_PIN = 27

def card_read_callback(bits, value):
    print(f"Kart UID: {value}  (bit sayısı: {bits})")

w = WiegandDecoder(DATA0_PIN, DATA1_PIN, card_read_callback)
print("Kart okuyucu aktif...")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
