import pyautogui
import time
import random
import config


def move_piece(move, board_region, board_flipped=False):
    """
    Executes a move on the screen by clicking the source and target squares.

    Args:
        move (str): Move in UCI format (e.g., "e2e4").
        board_region (tuple): (left, top, width, height)
        board_flipped (bool): True jika board dibalik (bermain sebagai hitam).
                              Saat flipped: file a di kanan, rank 1 di atas.
    """
    if not move or len(move) < 4:
        return

    left, top, width, height = board_region
    sq_w = width  / 8
    sq_h = height / 8

    # Ketika normal (putih di bawah): file a = col 0 (kiri), rank 8 = row 0 (atas)
    # Ketika flipped (hitam di bawah): file a = col 7 (kanan), rank 8 = row 7 (bawah)
    file_map = {c: i for i, c in enumerate('abcdefgh')}  # a=0 .. h=7
    rank_map = {str(r): 8 - r for r in range(1, 9)}      # '1'=7 .. '8'=0

    if board_flipped:
        # Balik kolom dan baris
        file_map = {c: 7 - i for i, c in enumerate('abcdefgh')}  # a=7 .. h=0
        rank_map = {str(r): r - 1 for r in range(1, 9)}          # '1'=0 .. '8'=7

    try:
        src_file, src_rank = move[0], move[1]
        dst_file, dst_rank = move[2], move[3]

        src_x = left + (file_map[src_file] + 0.5) * sq_w
        src_y = top  + (rank_map[src_rank] + 0.5) * sq_h
        dst_x = left + (file_map[dst_file] + 0.5) * sq_w
        dst_y = top  + (rank_map[dst_rank] + 0.5) * sq_h

        print(f"Moving mouse: {move}")

        pyautogui.moveTo(src_x, src_y, duration=config.MOUSE_DURATION)
        pyautogui.click()
        time.sleep(config.CLICK_DELAY)
        pyautogui.moveTo(dst_x, dst_y, duration=config.MOUSE_DURATION)
        pyautogui.click()

    except KeyError as e:
        print(f"Error parsing move coordinates: {e}")
