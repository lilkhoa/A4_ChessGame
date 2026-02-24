from pieces.base_piece import Piece

class Rook(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "rook"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        # Bốn hướng ngang dọc
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_linear_moves(board, current_row, current_col, directions)