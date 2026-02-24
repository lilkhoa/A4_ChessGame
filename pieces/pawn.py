from pieces.base_piece import Piece

class Pawn(Piece):
    def __init__(self, color: str):
        super().__init__(color)
        self.name = "pawn"
        # Giả sử Trắng ở dưới (row 6) đi lên (giảm row), Đen ở trên (row 1) đi xuống (tăng row)
        self.direction = -1 if self.color == "white" else 1

    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        moves = []
        
        # 1. Di chuyển thẳng lên 1 ô
        r = current_row + self.direction
        if 0 <= r < 8 and board[r][current_col] is None:
            moves.append((r, current_col))
            
            # 2. Di chuyển thẳng lên 2 ô (chỉ khi chưa di chuyển lần nào và ô trước đó trống)
            if not self.has_moved:
                r2 = current_row + 2 * self.direction
                if 0 <= r2 < 8 and board[r2][current_col] is None:
                    moves.append((r2, current_col))

        # 3. Ăn chéo (trái và phải)
        for dc in [-1, 1]:
            c = current_col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                if target_piece is not None and self.is_enemy(target_piece):
                    moves.append((r, c))
                    
        # Lưu ý: Bắt tốt qua đường (En Passant) sẽ cần biết lịch sử ván đấu (nước đi ngay trước đó). 
        # Logic này nên được chèn ở rules.py hoặc game_state.py bằng cách lọc thêm vào mảng moves này.

        return moves