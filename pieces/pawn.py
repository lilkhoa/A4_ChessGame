from pieces.base_piece import Piece

class Pawn(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "pawn"
        self.direction = -1 if self.color == "white" else 1

    def get_valid_moves(self, board, current_row: int, current_col: int, last_move=None) -> list:
        moves = []
        r = current_row + self.direction
        
        if 0 <= r < 8 and board[r][current_col] is None:
            moves.append((r, current_col))
            if not self.has_moved:
                r2 = current_row + 2 * self.direction
                if 0 <= r2 < 8 and board[r2][current_col] is None:
                    moves.append((r2, current_col))

        for dc in [-1, 1]:
            c = current_col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                if target_piece is not None and self.is_enemy(target_piece):
                    moves.append((r, c))
                elif last_move and target_piece is None:
                    last_p = last_move["piece"]
                    last_start = last_move["start"]
                    last_end = last_move["end"]
                    if last_p.name == "pawn" and abs(last_start[0] - last_end[0]) == 2:
                        if last_end[0] == current_row and last_end[1] == c:
                            moves.append((r, c))

        return moves