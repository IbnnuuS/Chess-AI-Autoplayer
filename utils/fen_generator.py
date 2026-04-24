def generate_fen(board_matrix):
    """
    Converts an 8x8 matrix of pieces into the piece placement part of a FEN string.
    
    Args:
        board_matrix (list): 8x8 list where each element is a FEN char or None for empty.
                             Ordered from rank 8 to rank 1 (top to bottom).
    
    Returns:
        str: FEN piece placement string (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
    """
    fen_rows = []
    
    for row in board_matrix:
        empty_count = 0
        row_str = ""
        for square in row:
            if square is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    row_str += str(empty_count)
                    empty_count = 0
                row_str += square
        if empty_count > 0:
            row_str += str(empty_count)
        fen_rows.append(row_str)
    
    return "/".join(fen_rows)
