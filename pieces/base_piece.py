from abc import ABC, abstractmethod

class Piece(ABC):
    def __init__(self, color: str):
        """
        color: 'white' hoặc 'black'
        """
        self.color = color
        self.has_moved = False # Rất quan trọng cho Nhập thành (King, Rook) và đi 2 ô (Pawn)
        self.name = "piece"

    @abstractmethod
    def get_valid_moves(self, board, current_row: int, current_col: int) -> list:
        """
        Trả về danh sách các tuple (row, col) thể hiện các nước đi hợp lệ của quân cờ.
        board: Mảng 2 chiều 8x8 chứa các object Piece hoặc None.
        """
        pass

    def is_enemy(self, other_piece) -> bool:
        """Kiểm tra xem ô đích có phải là quân địch không."""
        return other_piece is not None and self.color != other_piece.color

    def _get_linear_moves(self, board, current_row: int, current_col: int, directions: list) -> list:
        """
        Hàm helper dùng cho Rook, Bishop, Queen để lấy các nước đi theo các hướng trượt dài.
        """
        moves = []
        for dr, dc in directions:
            r, c = current_row + dr, current_col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                if target_piece is None:
                    # Ô trống, có thể đi
                    moves.append((r, c))
                elif self.is_enemy(target_piece):
                    # Có quân địch, có thể ăn nhưng không thể đi tiếp qua mặt
                    moves.append((r, c))
                    break
                else:
                    # Có quân ta, bị chặn
                    break
                r += dr
                c += dc
        return moves

    def __repr__(self):
        return f"{self.color}_{self.name}"