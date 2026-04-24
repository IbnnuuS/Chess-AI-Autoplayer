import cv2
import numpy as np
import os
from config import ASSETS_DIR, PIECE_MAP, CONFIDENCE_THRESHOLD


def split_board_into_64_squares(board_image):
    """
    Memotong gambar papan menjadi 8x8 = 64 kotak.
    Menggunakan float-boundary untuk menghindari akumulasi error pembulatan.
    """
    height, width = board_image.shape[:2]
    sq_h = height / 8
    sq_w = width  / 8

    squares = []
    for i in range(8):
        row = []
        for j in range(8):
            y0 = round(i * sq_h)
            y1 = round((i + 1) * sq_h)
            x0 = round(j * sq_w)
            x1 = round((j + 1) * sq_w)
            row.append(board_image[y0:y1, x0:x1])
        squares.append(row)

    return squares


def _load_templates():
    """
    Muat semua template dari folder assets.
    Returns: dict {label: [grayscale images]}
    """
    templates = {}

    for label in PIECE_MAP.keys():
        if label == 'empty':
            continue

        variants = []

        # Pion: ada template per-kolom (bp_col0 .. bp_col7)
        if label in ('bp', 'wp'):
            for col_idx in range(8):
                path = os.path.join(ASSETS_DIR, f"{label}_col{col_idx}.png")
                if os.path.exists(path):
                    img = cv2.imread(path)
                    if img is not None:
                        variants.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

        # Semua bidak: varian light / dark
        for variant in ['light', 'dark']:
            path = os.path.join(ASSETS_DIR, f"{label}_{variant}.png")
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    variants.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

        # Fallback: file tanpa suffix
        if not variants:
            path_old = os.path.join(ASSETS_DIR, f"{label}.png")
            if os.path.exists(path_old):
                img = cv2.imread(path_old)
                if img is not None:
                    variants.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

        if variants:
            templates[label] = variants
        else:
            print(f"Warning: Tidak ada template untuk '{label}'")

    return templates


# Cache template
_TEMPLATE_CACHE = None


def detect_pieces(squares):
    """
    Template matching tiap kotak vs semua template.
    Kotak dianggap terisi bidak jika skor >= CONFIDENCE_THRESHOLD.
    """
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        _TEMPLATE_CACHE = _load_templates()
    templates = _TEMPLATE_CACHE

    board_matrix = []

    for row_squares in squares:
        matrix_row = []
        for square in row_squares:
            sq_gray = cv2.cvtColor(square, cv2.COLOR_BGR2GRAY)

            best_match = None
            max_val    = -1

            for label, variant_list in templates.items():
                for tmpl in variant_list:
                    if tmpl.shape[:2] != sq_gray.shape[:2]:
                        tmpl = cv2.resize(tmpl, (sq_gray.shape[1], sq_gray.shape[0]))
                    res = cv2.matchTemplate(sq_gray, tmpl, cv2.TM_CCOEFF_NORMED)
                    _, val, _, _ = cv2.minMaxLoc(res)
                    if val > max_val:
                        max_val    = val
                        best_match = label

            if max_val >= CONFIDENCE_THRESHOLD:
                matrix_row.append(PIECE_MAP[best_match])
            else:
                matrix_row.append(None)

        board_matrix.append(matrix_row)

    return board_matrix


def reload_templates():
    """Paksa reload template."""
    global _TEMPLATE_CACHE
    _TEMPLATE_CACHE = None
