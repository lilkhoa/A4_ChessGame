from pieces.base_piece import Piece

class King(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "king"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        moves = []
        # Tám hướng xung quanh Vua (đi 1 bước)
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        for dr, dc in directions:
            r, c = current_row + dr, current_col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                if target_piece is None or self.is_enemy(target_piece):
                    moves.append((r, c))

        # Lưu ý: Logic Nhập thành (Castling) cần kiểm tra xem Vua có đang bị chiếu không, 
        # các ô Vua đi qua có bị kiểm soát không. Nên giống như En Passant của Tốt, 
        # logic đó sẽ do rules.py hoặc board.py bổ sung. Ở cấp độ piece, Vua chỉ cần biết nó đi được 1 ô.

        return moves