def is_under_attack(board, r, c, enemy_color):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.color == enemy_color:
                if piece.name == "pawn":
                    pseudo_moves = piece.get_valid_moves(board, row, col, None)
                else:
                    pseudo_moves = piece.get_valid_moves(board, row, col)
                if (r, c) in pseudo_moves:
                    return True
    return False

def is_in_check(board, color):
    king_pos = None
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece.name == "king" and piece.color == color:
                king_pos = (r, c)
                break
        if king_pos:
            break
            
    if not king_pos:
        return False
        
    enemy_color = "black" if color == "white" else "white"
    return is_under_attack(board, king_pos[0], king_pos[1], enemy_color)

def get_legal_moves(board, piece, r, c, last_move=None):
    if piece.name == "pawn":
        pseudo_moves = piece.get_valid_moves(board, r, c, last_move)
    else:
        pseudo_moves = piece.get_valid_moves(board, r, c)
        
    legal_moves = []
    
    for mr, mc in pseudo_moves:
        if piece.name == "king" and abs(mc - c) == 2:
            if is_in_check(board, piece.color):
                continue
            step = 1 if mc > c else -1
            board[r][c + step] = piece
            board[r][c] = None
            in_check_mid = is_in_check(board, piece.color)
            board[r][c] = piece
            board[r][c + step] = None
            if in_check_mid:
                continue

        target_piece = board[mr][mc]
        en_passant_cap = None
        
        if piece.name == "pawn" and mc != c and target_piece is None:
            en_passant_cap = board[r][mc]
            board[r][mc] = None

        board[mr][mc] = piece
        board[r][c] = None
        
        if not is_in_check(board, piece.color):
            legal_moves.append((mr, mc))
            
        board[r][c] = piece
        board[mr][mc] = target_piece
        
        if en_passant_cap:
            board[r][mc] = en_passant_cap
            
    return legal_moves

def is_checkmate(board, color, last_move=None):
    if not is_in_check(board, color):
        return False
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece.color == color:
                if get_legal_moves(board, piece, r, c, last_move):
                    return False
    return True

def is_stalemate(board, color, last_move=None):
    if is_in_check(board, color):
        return False
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece.color == color:
                if get_legal_moves(board, piece, r, c, last_move):
                    return False
    return True