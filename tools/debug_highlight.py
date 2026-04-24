"""
Tool kalibrasi warna highlight chess.com.
Jalankan setelah lawan/kamu sudah bergerak (ada kotak berwarna di layar).
Akan mencetak nilai HSV rata-rata setiap kotak beserta rasio warna.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import cv2
import numpy as np
from capture.screenshot import capture_board
from vision.detect_board import split_board_into_64_squares
import config

def main():
    print("Mengambil screenshot...")
    img  = capture_board(config.BOARD_REGION)
    sqs  = split_board_into_64_squares(img)
    files = 'abcdefgh'

    print("\nNilai HSV rata-rata setiap kotak + rasio kuning & biru:")
    print(f"{'Kotak':<6} {'H_avg':>6} {'S_avg':>6} {'V_avg':>6} {'Y_ratio':>8} {'B_ratio':>8}")
    print("-" * 48)

    LOWER_Y = np.array([10,  50, 160])
    UPPER_Y = np.array([40, 255, 255])
    LOWER_B = np.array([85,  15,  80])
    UPPER_B = np.array([130, 200, 230])
    RATIO_MIN = 0.15
    S_AVG_MIN = 45

    suspects = []
    for r in range(8):
        for c in range(8):
            sq      = sqs[r][c]
            sq_hsv  = cv2.cvtColor(sq, cv2.COLOR_BGR2HSV)
            total   = sq_hsv.shape[0] * sq_hsv.shape[1]
            h_avg   = float(sq_hsv[:, :, 0].mean())
            s_avg   = float(sq_hsv[:, :, 1].mean())
            v_avg   = float(sq_hsv[:, :, 2].mean())
            y_ratio = cv2.countNonZero(cv2.inRange(sq_hsv, LOWER_Y, UPPER_Y)) / total
            b_ratio = cv2.countNonZero(cv2.inRange(sq_hsv, LOWER_B, UPPER_B)) / total

            name = f"{files[c]}{8-r}"
            # Tampilkan semua yang punya rasio > 0.02 (lebih rendah dari threshold agar kita lihat kandidat)
            if y_ratio > 0.02 or b_ratio > 0.02:
                would_detect = (y_ratio >= RATIO_MIN or b_ratio >= RATIO_MIN) and s_avg >= S_AVG_MIN
                suspects.append((name, h_avg, s_avg, v_avg, y_ratio, b_ratio, would_detect))

    if suspects:
        for name, h, s, v, y, b, detect in suspects:
            print(f"{name:<6} {h:>6.1f} {s:>6.1f} {v:>6.1f} {y:>8.3f} {b:>8.3f} {'(DETECTED)' if detect else ''}")
        print(f"\n✅ Ditemukan {len(suspects)} kotak dengan kemungkinan highlight.")
        print("Kotak kuning: Y_ratio harus >= 0.08")
        print("Kotak biru:   B_ratio harus >= 0.08")
    else:
        print("Tidak ada kotak yang terdeteksi sebagai highlight.")
        print("Pastikan ada kotak berwarna di papan sebelum menjalankan tool ini.")

if __name__ == "__main__":
    main()
