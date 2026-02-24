class Move:
    def __init__(self, start_sq, end_sq, board_grid):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        
        self.piece_moved = board_grid[self.start_row][self.start_col]
        self.piece_captured = board_grid[self.end_row][self.end_col]
        
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False