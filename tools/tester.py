import pyautogui
import time
import os
import sys
import cv2

# Menambahkan path project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from capture.screenshot import capture_board
from vision.detect_board import split_board_into_64_squares, detect_pieces

def test_mouse():
    print("--- TESTING MOUSE ---")
    print("Mouse akan bergerak membentuk kotak di tengah layar dalam 3 detik...")
    time.sleep(3)
    screen_w, screen_h = pyautogui.size()
    cx, cy = screen_w // 2, screen_h // 2
    
    try:
        pyautogui.moveTo(cx - 100, cy - 100, duration=0.5)
        pyautogui.moveTo(cx + 100, cy - 100, duration=0.5)
        pyautogui.moveTo(cx + 100, cy + 100, duration=0.5)
        pyautogui.moveTo(cx - 100, cy + 100, duration=0.5)
        pyautogui.moveTo(cx, cy, duration=0.5)
        print("Mouse test selesai. Apakah kamu melihat mouse bergerak?")
    except Exception as e:
        print(f"Mouse Error: {e}")

def test_vision():
    import os
    from config import ASSETS_DIR, PIECE_MAP, CONFIDENCE_THRESHOLD

    print("\n--- TESTING VISION ---")
    if not os.path.exists(config.ASSETS_DIR):
        print("Error: Folder assets tidak ada!")
        return

    print(f"Mengambil gambar dengan BOARD_REGION: {config.BOARD_REGION}")
    board_img = capture_board(config.BOARD_REGION)
    cv2.imwrite("test_capture.png", board_img)

    # Visualisasi Grid
    debug_img = board_img.copy()
    h, w = debug_img.shape[:2]
    for i in range(1, 8):
        cv2.line(debug_img, (i * w // 8, 0), (i * w // 8, h), (0, 0, 255), 2)
        cv2.line(debug_img, (0, i * h // 8), (w, i * h // 8), (0, 0, 255), 2)
    cv2.imwrite("debug_grid.png", debug_img)
    print("Grid visualisasi disimpan ke 'debug_grid.png'. Buka file ini!")

    squares = split_board_into_64_squares(board_img)

    # Load templates (sama dengan detect_board.py)
    templates = {}
    for label in PIECE_MAP.keys():
        if label == 'empty':
            continue
        variants = []

        # Pion: cek semua 8 kolom terlebih dahulu
        if label in ('bp', 'wp'):
            for col_idx in range(8):
                path = os.path.join(config.ASSETS_DIR, f"{label}_col{col_idx}.png")
                if os.path.exists(path):
                    img = cv2.imread(path)
                    if img is not None:
                        variants.append((label, f"col{col_idx}", img))

        # Semua bidak: cek juga varian light/dark
        for variant in ['light', 'dark']:
            path = os.path.join(config.ASSETS_DIR, f"{label}_{variant}.png")
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    variants.append((label, variant, img))
            elif variant == 'light':
                path_old = os.path.join(config.ASSETS_DIR, f"{label}.png")
                if os.path.exists(path_old):
                    img = cv2.imread(path_old)
                    if img is not None:
                        variants.append((label, variant, img))

        templates[label] = variants

    files = 'abcdefgh'
    ranks = '87654321'
    board_matrix   = []
    score_matrix   = []
    problem_squares = []

    for r in range(8):
        matrix_row = []
        score_row  = []
        for c in range(8):
            square      = squares[r][c]
            square_gray = cv2.cvtColor(square, cv2.COLOR_BGR2GRAY)
            best_label  = None
            best_var    = None
            max_val     = -1

            for label, var_list in templates.items():
                for (lbl, var, tmpl) in var_list:
                    tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
                    if tmpl_gray.shape[:2] != square_gray.shape[:2]:
                        tmpl_gray = cv2.resize(tmpl_gray, (square_gray.shape[1], square_gray.shape[0]))
                    res = cv2.matchTemplate(square_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                    _, val, _, _ = cv2.minMaxLoc(res)
                    if val > max_val:
                        max_val     = val
                        best_label  = lbl
                        best_var    = var

            detected = PIECE_MAP[best_label] if max_val >= CONFIDENCE_THRESHOLD else None
            matrix_row.append(detected)
            score_row.append((best_label, best_var, max_val))

            sq_name = f"{files[c]}{ranks[r]}"
            if detected is None and max_val > 0.4:
                problem_squares.append((sq_name, best_label, best_var, max_val))

        board_matrix.append(matrix_row)
        score_matrix.append(score_row)

    print("\nMatrix Papan Terdeteksi (Rank 8 ke 1):")
    for row in board_matrix:
        print([p if p else '.' for p in row])

    print(f"\nThreshold saat ini: {CONFIDENCE_THRESHOLD}")
    
    if problem_squares:
        print("\n⚠️  Kotak yang HAMPIR terdeteksi (skor di bawah threshold):")
        print(f"{'Kotak':<8} {'Template':<12} {'Variant':<8} {'Score':<8}")
        print("-" * 40)
        for sq, lbl, var, score in sorted(problem_squares, key=lambda x: -x[3]):
            print(f"{sq:<8} {lbl:<12} {var:<8} {score:.4f}")
    else:
        print("\n✅ Semua kotak terdeteksi dengan baik!")

if __name__ == "__main__":
    test_mouse()
    test_vision()
