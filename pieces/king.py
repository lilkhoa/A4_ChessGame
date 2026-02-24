from pieces.base_piece import Piece

class King(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "king"

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        moves = []
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

        if not self.has_moved:
            right_rook = board[current_row][7]
            if right_rook and right_rook.name == "rook" and not right_rook.has_moved:
                if board[current_row][5] is None and board[current_row][6] is None:
                    moves.append((current_row, 6))
                    
            left_rook = board[current_row][0]
            if left_rook and left_rook.name == "rook" and not left_rook.has_moved:
                if board[current_row][1] is None and board[current_row][2] is None and board[current_row][3] is None:
                    moves.append((current_row, 2))

        return moves