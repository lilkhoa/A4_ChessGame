from pieces.base_piece import Piece

class Bishop(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "bishop"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        # Bốn hướng chéo
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_linear_moves(board, current_row, current_col, directions)