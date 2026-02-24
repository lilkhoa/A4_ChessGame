from pieces.base_piece import Piece

class Knight(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "knight"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        moves = []
        # 8 vị trí chữ L mà Mã có thể nhảy tới
        knight_jumps = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]

        for dr, dc in knight_jumps:
            r, c = current_row + dr, current_col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                # Có thể đi vào ô trống hoặc ô chứa quân địch
                if target_piece is None or self.is_enemy(target_piece):
                    moves.append((r, c))

        return moves