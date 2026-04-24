import time
import random
import cv2
import numpy as np
import chess
from capture.screenshot import capture_board
from vision.detect_board import split_board_into_64_squares, detect_pieces
from utils.fen_generator import generate_fen
from engine.stockfish_agent import get_best_move, close_engine
from automation.click_controller import move_piece
import config

# Global: apakah papan dibalik (bermain sebagai hitam)?
BOARD_FLIPPED = (config.MY_COLOR == 'b')


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_screenshot(apply_rotation=True):
    """Ambil raw screenshot papan. Jika hitam dan apply_rotation=True, rotasi 180° untuk logik warna highlight."""
    img = capture_board(config.BOARD_REGION)
    if BOARD_FLIPPED and apply_rotation:
        img = cv2.rotate(img, cv2.ROTATE_180)
    return img


def detect_player_color():
    """Deteksi apakah main putih atau hitam dari posisi bidak di bawah."""
    print("Mendeteksi warna pemain dari layar...")
    # Ambil raw screenshot (kita butuh keadaan asli di layar, tanpa rotasi)
    img = capture_board(config.BOARD_REGION)
    squares = split_board_into_64_squares(img)
    m = detect_pieces(squares)

    white_count = 0
    black_count = 0
    # Cek 2 baris paling bawah dari papan visual (baris ke-6 dan ke-7)
    for r in [6, 7]:
        for c in range(8):
            piece = m[r][c]
            if piece is not None:
                if piece.isupper():
                    white_count += 1
                elif piece.islower():
                    black_count += 1

    if black_count > white_count:
        print("  -> Terdeteksi bermain sebagai HITAM (papan dibalik)")
        return 'b'
    else:
        print("  -> Terdeteksi bermain sebagai PUTIH")
        return 'w'


def count_pieces(matrix):
    return sum(1 for row in matrix for sq in row if sq is not None)


def detect_stable_matrix(attempts=3, interval=0.4):
    """Ambil matrix N kali, pilih yang paling banyak bidak."""
    best, best_n = None, -1
    for _ in range(attempts):
        img = get_screenshot(apply_rotation=False)  # Jangan rotasi gambar, agar template tidak terbalik
        squares = split_board_into_64_squares(img)
        m = detect_pieces(squares)
        
        # Jika main hitam, matriknya kita putar 180 derajat setelah dideteksi
        if BOARD_FLIPPED:
            m = [row[::-1] for row in m[::-1]]
            
        n = count_pieces(m)
        if n > best_n:
            best_n, best = n, m
        time.sleep(interval)
    return best


def detect_highlighted_squares(debug=False):
    """
    Deteksi kotak yang di-highlight chess.com (kuning/biru).
    Chess.com Hijau theme:
      - Kotak ASAL (FROM, sudah kosong) = kuning penuh (S_avg > 100, ratio > 0.80)
      - Kotak TUJUAN (TO, ada bidak)    = kuning redup (S_avg ~60-90, ratio ~0.03-0.06)
    Kunci: tambah filter S_avg >= 50 agar kotak krem/shadow tidak ikut terdeteksi.

    Returns: list of (row, col) semua kotak yang highlight.
    """
    board_img = get_screenshot()
    squares   = split_board_into_64_squares(board_img)

    # Kuning/olive chess.com:
    # - Kotak hijau biasa: V (brightness) selalu di bawah ~155
    # - Kotak cerah biasa: S (saturation) selalu di bawah ~40
    # - Highlight KUNING: V >= 160 dan S >= 50, H antara 10-40
    LOWER_YELLOW = np.array([10,  50, 160])
    UPPER_YELLOW = np.array([40, 255, 255])
    LOWER_BLUE   = np.array([85,  15,  80])
    UPPER_BLUE   = np.array([130, 200, 230])
    RATIO_MIN    = 0.15    # Ditingkatkan dari 0.02 → abaikan noise (biasanya noise y_ratio cuma 0.02-0.05)
    S_AVG_MIN    = 45      # Filter kotak abu-abu/putih murni

    highlighted = []
    files = 'abcdefgh'

    for r in range(8):
        for c in range(8):
            sq_hsv = cv2.cvtColor(squares[r][c], cv2.COLOR_BGR2HSV)
            total  = sq_hsv.shape[0] * sq_hsv.shape[1]
            s_avg  = float(sq_hsv[:, :, 1].mean())

            y_ratio = cv2.countNonZero(cv2.inRange(sq_hsv, LOWER_YELLOW, UPPER_YELLOW)) / total
            b_ratio = cv2.countNonZero(cv2.inRange(sq_hsv, LOWER_BLUE,   UPPER_BLUE))   / total

            if (y_ratio >= RATIO_MIN or b_ratio >= RATIO_MIN) and s_avg >= S_AVG_MIN:
                highlighted.append((r, c))
                if debug:
                    sq_name = f"{files[c]}{8-r}"
                    print(f"    HIGHLIGHT {sq_name}: y={y_ratio:.3f} b={b_ratio:.3f} S={s_avg:.1f}")

    return highlighted


def wait_for_opponent_move(our_squares, timeout=120):
    """
    Polling sampai muncul 2 kotak highlight yang BERBEDA dari langkah kita.
    Setiap 4 detik, program juga mengecek layar apakah ada popup "Game Over" 
    yang menutupi papan.
    """
    our_set  = frozenset(map(tuple, our_squares))
    deadline = time.time() + timeout
    last_visual_check = time.time()

    while time.time() < deadline:
        hl  = detect_highlighted_squares()
        new = [sq for sq in hl if tuple(sq) not in our_set]

        # Tunggu sampai ada tepat 2 kotak baru yang berbeda dari langkah kita
        if len(new) == 2:
            return new

        # Jika total highlight = 2 dan berbeda dari kita → juga valid
        if len(hl) == 2 and frozenset(map(tuple, hl)) != our_set:
            return hl

        # Cek secara visual jika musuh menyerah (papan tertutup popup / meredup)
        # Efeknya, jumlah bidak yang terdeteksi drastis turun
        if time.time() - last_visual_check > 4.0:
            last_visual_check = time.time()
            img = get_screenshot(apply_rotation=False)
            m = detect_pieces(split_board_into_64_squares(img))
            n = count_pieces(m)
            # Jika tiba-tiba sangat sedikit / 0 bidak tapi highlight tak berubah,
            # sangat besar kemungkinan layar ditutup popup end game "Resigned/Won"
            if n < 5:
                print(f"  [Deteksi Visual] Tiba-tiba bidak hilang/papan tertutup (sisa {n} bidak). Popup Game Over muncul?")
                return "GAME_OVER_DETECTED"

        time.sleep(0.4)

    return None


def build_initial_board():
    print("Mendeteksi posisi awal...")
    best_matrix, best_n = None, -1
    for _ in range(5):
        img = get_screenshot(apply_rotation=False) # Jangan rotasi gambar
        sq  = split_board_into_64_squares(img)
        m   = detect_pieces(sq)
        
        if BOARD_FLIPPED:
            # Putar matriks 180 derajat agar rank 8 ada di baris index 0
            m = [row[::-1] for row in m[::-1]]
            
        n   = count_pieces(m)
        if n > best_n:
            best_n, best_matrix = n, m
        time.sleep(0.4)

    print(f"  Terdeteksi {best_n} bidak.")
    if best_n >= 20:
        placement = generate_fen(best_matrix)
        fen = f"{placement} {config.MY_COLOR} KQkq - 0 1"
        try:
            b = chess.Board(fen)
            wk    = len(b.pieces(chess.KING, chess.WHITE))
            bk    = len(b.pieces(chess.KING, chess.BLACK))
            total = sum(len(b.pieces(pt, c))
                        for pt in chess.PIECE_TYPES
                        for c in [chess.WHITE, chess.BLACK])
            if wk == 1 and bk == 1 and total <= 32:
                print(f"  Posisi: {fen}")
                return b
            print(f"  Posisi tidak valid (raja w={wk} b={bk}, total={total}).")
            print("  → Pastikan capture_pieces.py dijalankan di posisi AWAL game.")
            print("  → Pakai posisi standar untuk sesi ini.")
        except Exception as e:
            print(f"  FEN tidak valid ({e}), pakai posisi standar.")

    b = chess.Board()
    print(f"  Posisi standar: {b.fen()}")
    return b

def squares_to_uci(sq_list, board):
    """
    Terjemahkan 2 kotak highlight ke UCI.
    Coba kedua arah (a→b atau b→a) dan pilih yang legal.
    """
    if len(sq_list) != 2:
        return None
    files = 'abcdefgh'
    (r1, c1), (r2, c2) = sq_list
    for uci in [f"{files[c1]}{8-r1}{files[c2]}{8-r2}",
                f"{files[c2]}{8-r2}{files[c1]}{8-r1}"]:
        try:
            mv = chess.Move.from_uci(uci)
            if mv in board.legal_moves:
                return uci
        except Exception:
            pass
    return None


def uci_to_squares(uci, board_flipped=False):
    """
    Hitung 2 kotak (row, col) dari string UCI langkah kita.
    Digunakan sebagai referensi 'our_highlight' tanpa deteksi visual,
    menghindari race condition jika lawan merespons sangat cepat.
    """
    f = 'abcdefgh'
    sf, sr = f.index(uci[0]), int(uci[1])
    df, dr = f.index(uci[2]), int(uci[3])
    if not board_flipped:
        return [(8 - sr, sf), (8 - dr, df)]
    else:
        return [(sr - 1, 7 - sf), (dr - 1, 7 - df)]


# ─────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────

def main():
    print("=" * 50)
    print("       CHESS AI AUTOPLAYER STARTED")
    print("=" * 50)
    print(f"Stockfish : {config.STOCKFISH_PATH}")
    print(f"Board     : {config.BOARD_REGION}")
    
    # Deteksi warna pemain secara otomatis di awal
    detected_color = detect_player_color()
    config.MY_COLOR = detected_color
    
    global BOARD_FLIPPED
    BOARD_FLIPPED = (config.MY_COLOR == 'b')
    MY_COLOR = chess.WHITE if config.MY_COLOR == 'w' else chess.BLACK

    print(f"Warna     : {'Putih' if config.MY_COLOR == 'w' else 'Hitam'}")
    print()

    board    = build_initial_board()

    # Kotak biru dari langkah sebelumnya (dimulai kosong)
    our_blue = []
    time.sleep(1)

    print("\nSiap!\n")

    while not board.is_game_over():
        try:
            it_is_my_turn = (board.turn == MY_COLOR)

            # ─── GILIRAN SAYA ────────────────────────────
            if it_is_my_turn:
                print("[GILIRAN SAYA]")
                fen = board.fen()
                print(f"  FEN : {fen}")

                best_move = get_best_move(fen, config.STOCKFISH_PATH, config.ENGINE_DEPTH)
                if not best_move:
                    print("  Stockfish tidak menemukan langkah. Menunggu 3s...")
                    time.sleep(3)
                    continue

                print(f"  → {best_move}")
                delay = random.uniform(*config.MOVE_DELAY)
                time.sleep(delay)

                move_piece(best_move, config.BOARD_REGION, board_flipped=BOARD_FLIPPED)
                board.push_uci(best_move)

                if board.is_checkmate():
                    print("  !!! SKAKMAT !!! Kita menang.")
                    break
                elif board.is_check():
                    print("  !!! SKAK !!! (Mengawasi jika lawan menyerah)")

                # Hitung kotak highlight kita dari UCI (tanpa perlu deteksi visual)
                # Ini menghindari race condition jika lawan merespons sangat cepat
                our_blue = uci_to_squares(best_move, board_flipped=BOARD_FLIPPED)
                print(f"  Highlight kita: {our_blue}")
                time.sleep(0.8)  # Beri waktu animasi sebelum mulai polling
                print("  Menunggu langkah lawan...")

            # ─── MENUNGGU LAWAN ──────────────────────────
            else:
                print("  [menunggu lawan]")
                new_squares = wait_for_opponent_move(our_blue, timeout=120)

                if new_squares == "GAME_OVER_DETECTED":
                    print("  Game Over / Lawan menyerah terdeteksi secara visual!")
                    break
                elif new_squares is None:
                    print("  Timeout menunggu lawan.")
                    break

                print(f"  Kotak lawan: {new_squares}")
                opp_uci = squares_to_uci(new_squares, board)
                if opp_uci:
                    board.push_uci(opp_uci)
                    print(f"  Langkah lawan: {opp_uci}")
                    our_blue = new_squares
                else:
                    # Tidak bisa terjemahkan blue → kemungkinan castling, promosi, atau deteksi palsu
                    # Cari langkah dari matrix sebagai fallback HANYA untuk update board state
                    print("  Blue tak terbaca. Coba inferensi dari matrix...")
                    time.sleep(0.5)
                    after_m = detect_stable_matrix(attempts=3)
                    n = count_pieces(after_m)
                    if n >= 20:
                        # Coba cari langkah dari perbedaan state sebelum vs sesudah
                        prev_fen_board = board.copy()
                        found = False
                        for mv in prev_fen_board.legal_moves:
                            test_board = prev_fen_board.copy()
                            test_board.push(mv)
                            placement = generate_fen(after_m)
                            if test_board.board_fen() == chess.Board(
                                f"{placement} w KQkq - 0 1"
                            ).board_fen():
                                board.push(mv)
                                print(f"  Langkah lawan (dari matrix): {mv.uci()}")
                                found = True
                                break
                        if not found:
                            # Tidak bisa cari langkah spesifik →
                            # Paksa giliran ke kita tanpa push (hanya update referensi biru)
                            print("  Tidak bisa mengidentifikasi langkah lawan, lanjut giliran kita.")
                    else:
                        print(f"  Matrix juga tidak terbaca ({n} bidak), lanjut giliran kita.")
                    our_blue = new_squares

        except KeyboardInterrupt:
            print("\nProgram dihentikan.")
            close_engine()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)

    print("\nGame selesai!")
    if board.is_game_over():
        print(f"Hasil: {board.result()}")
    close_engine()


if __name__ == "__main__":
    main()
