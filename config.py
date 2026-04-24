import os

# --- PATH CONFIGURATION ---
# Path to your Stockfish executable (e.g., "C:/stockfish/stockfish-windows-x86-64-avx2.exe")
STOCKFISH_PATH = "C:\stockfish\stockfish-windows-x86-64-avx2.exe" 

# Directory for piece templates
ASSETS_DIR = "assets"

# --- ENGINE CONFIGURATION ---
ENGINE_DEPTH = 10
MOVE_DELAY = (0.5, 1.5)  # Jeda (delay) acak sebelum AI berpikir / klik jalan (dalam detik)

# --- MOUSE / CLICK CONFIGURATION ---
MOUSE_DURATION = 0.3      # Kecepatan lari kursor antara 0.1 s/d 0.5 detik
CLICK_DELAY = 0.1         # Jeda antara klik kotak awal ke kotak tujuan

MY_COLOR = 'w'  # 'w' = Putih (kamu di bawah), 'b' = Hitam (kamu di bawah, board flip)

# --- BOARD CONFIGURATION ---
# Screen region of the chess board: (left, top, width, height)
# You must calibrate this to your specific screen layout.
BOARD_REGION = (410, 233, 700, 700) 

# --- PIECE MAPPING ---
# Mapping of piece labels to FEN characters
PIECE_MAP = {
    'wp': 'P', 'wr': 'R', 'wn': 'N', 'wb': 'B', 'wq': 'Q', 'wk': 'K',
    'bp': 'p', 'br': 'r', 'bn': 'n', 'bb': 'b', 'bq': 'q', 'bk': 'k',
    'empty': None
}

# Detection Confidence Threshold
CONFIDENCE_THRESHOLD = 0.7
