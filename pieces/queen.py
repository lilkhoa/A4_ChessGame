from pieces.base_piece import Piece

class Queen(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "queen"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        # Tám hướng (ngang, dọc, chéo)
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),      # Như Xe
            (-1, -1), (-1, 1), (1, -1), (1, 1)     # Như Tượng
        ]
        return self._get_linear_moves(board, current_row, current_col, directions)