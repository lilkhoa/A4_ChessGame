class Move:
    def __init__(self, start_sq, end_sq, board_grid, is_en_passant=False, is_castle=False, is_promotion=False):

        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        
        self.piece_moved = board_grid[self.start_row][self.start_col]
        self.piece_captured = board_grid[self.end_row][self.end_col]
        
        self.move_id = (self.start_row * 1000) + (self.start_col * 100) + (self.end_row * 10) + (self.end_col)

        # Flags for special move
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.is_promotion = is_promotion
        self.promotion_piece = None  # Piece class to promote to (Queen, Rook, Bishop, Knight)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False
    
    def __str__(self):
        return f"Move({self.start_row},{self.start_col} -> {self.end_row},{self.end_col})"