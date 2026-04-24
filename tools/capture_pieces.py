import cv2
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capture.screenshot import capture_board
from vision.detect_board import split_board_into_64_squares
import config


def main():
    if not os.path.exists(config.ASSETS_DIR):
        os.makedirs(config.ASSETS_DIR)
        print(f"Folder {config.ASSETS_DIR} dibuat.")

    print(f"Mengambil screenshot di region: {config.BOARD_REGION}")
    board_img = capture_board(config.BOARD_REGION)
    cv2.imwrite("check_board.png", board_img)
    print("Screenshot papan disimpan ke 'check_board.png'.")

    squares = split_board_into_64_squares(board_img)

    # ─── Pion: simpan SEMUA 8 kolom (agar setiap posisi background terwakili) ───
    print("\nMenyimpan template pion dari semua 8 kolom...")
    for col in range(8):
        # Black pawn — rank 7 (row index 1)
        bp_path = os.path.join(config.ASSETS_DIR, f"bp_col{col}.png")
        cv2.imwrite(bp_path, squares[1][col])
        # White pawn — rank 2 (row index 6)
        wp_path = os.path.join(config.ASSETS_DIR, f"wp_col{col}.png")
        cv2.imwrite(wp_path, squares[6][col])
    print("  bp_col0 .. bp_col7 dan wp_col0 .. wp_col7 tersimpan.")

    # ─── Bidak lainnya: simpan dari posisi awal (light + dark) ───
    print("\nMenyimpan template bidak lainnya (light & dark)...")

    def is_light(row, col):
        return (row + col) % 2 == 0

    non_pawn_positions = [
        (0, 0, 'br'), (0, 1, 'bn'), (0, 2, 'bb'), (0, 3, 'bq'),
        (0, 4, 'bk'), (0, 5, 'bb'), (0, 6, 'bn'), (0, 7, 'br'),
        (7, 0, 'wr'), (7, 1, 'wn'), (7, 2, 'wb'), (7, 3, 'wq'),
        (7, 4, 'wk'), (7, 5, 'wb'), (7, 6, 'wn'), (7, 7, 'wr'),
    ]

    saved_light = set()
    saved_dark  = set()

    for row, col, label in non_pawn_positions:
        square_img = squares[row][col]
        sq_type = 'light' if is_light(row, col) else 'dark'

        if sq_type == 'light' and label not in saved_light:
            path = os.path.join(config.ASSETS_DIR, f"{label}_light.png")
            cv2.imwrite(path, square_img)
            print(f"  {path}")
            saved_light.add(label)
        elif sq_type == 'dark' and label not in saved_dark:
            path = os.path.join(config.ASSETS_DIR, f"{label}_dark.png")
            cv2.imwrite(path, square_img)
            print(f"  {path}")
            saved_dark.add(label)

    print("\nSelesai! Semua template tersimpan di folder 'assets'.")

    # ─── Kotak kosong: simpan sebagai baseline anti-false-positive ───
    # Rank 3 (row index 5) selalu kosong di posisi awal
    print("\nMenyimpan template kotak kosong (empty baseline)...")
    # a3 = row 5, col 0  → (5+0)%2=1 → 'dark' label (tapi warna asli: file a=1, rank 3: 1+3=4, even = LIGHT)
    # b3 = row 5, col 1  → (5+1)%2=0 → 'light' label
    # Simpan dua: satu light dan satu dark (nama berdasarkan tampilan)
    # Karena is_light di sini tidak penting, kita simpan dari a3 dan b3 saja
    empty_light_path = os.path.join(config.ASSETS_DIR, "empty_light.png")
    empty_dark_path  = os.path.join(config.ASSETS_DIR, "empty_dark.png")
    # b3 (row=5, col=1) → kotak terang (cream)
    cv2.imwrite(empty_light_path, squares[5][1])
    # a3 (row=5, col=0) → kotak gelap (hijau tua)
    cv2.imwrite(empty_dark_path,  squares[5][0])
    print(f"  {empty_light_path}")
    print(f"  {empty_dark_path}")
    print("\nSemua template selesai! Jalankan python tools/tester.py untuk verifikasi.")


if __name__ == "__main__":
    main()
