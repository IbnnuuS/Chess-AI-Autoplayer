import chess
import chess.engine

# Singleton engine instance agar tidak dibuka/ditutup setiap pemanggilan
_engine = None

def _get_engine(stockfish_path):
    """Mengembalikan instance engine Stockfish, membuat baru jika belum ada."""
    global _engine
    if _engine is None:
        _engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    return _engine


def get_best_move(fen, stockfish_path, depth=10):
    """
    Returns the best move in UCI format, or None on any error.
    Validates FEN before sending to engine to prevent crashes.
    """
    try:
        board = chess.Board(fen)

        # Validasi dasar: harus ada tepat 1 raja putih dan 1 raja hitam
        wk = len(board.pieces(chess.KING, chess.WHITE))
        bk = len(board.pieces(chess.KING, chess.BLACK))
        if wk != 1 or bk != 1:
            print(f"  FEN tidak valid: {wk} raja putih, {bk} raja hitam. Skip.")
            return None

        # Validasi jumlah bidak masuk akal
        total = sum(len(board.pieces(pt, c))
                    for pt in chess.PIECE_TYPES for c in [chess.WHITE, chess.BLACK])
        if total < 2 or total > 32:
            print(f"  FEN tidak valid: total bidak = {total}. Skip.")
            return None

        if not list(board.legal_moves):
            print("  Tidak ada langkah legal.")
            return None

        engine = _get_engine(stockfish_path)
        result = engine.play(board, chess.engine.Limit(depth=depth))
        return result.move.uci() if result.move else None

    except chess.engine.EngineTerminatedError:
        global _engine
        print("Engine Stockfish mati, mencoba restart...")
        _engine = None
        return None
    except Exception as e:
        print(f"Error communicating with Stockfish: {e}")
        return None


def close_engine():
    """Tutup engine Stockfish dengan bersih saat program selesai."""
    global _engine
    if _engine:
        _engine.quit()
        _engine = None
