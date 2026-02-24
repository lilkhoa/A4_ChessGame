from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self._setup_standard_board()

    def _setup_standard_board(self):
        self.grid[0] = [
            Rook("black"), Knight("black"), Bishop("black"), Queen("black"),
            King("black"), Bishop("black"), Knight("black"), Rook("black")
        ]
        
        self.grid[1] = [Pawn("black") for _ in range(8)]
        
        for r in range(2, 6):
            self.grid[r] = [None for _ in range(8)]
            
        self.grid[6] = [Pawn("white") for _ in range(8)]
        
        self.grid[7] = [
            Rook("white"), Knight("white"), Bishop("white"), Queen("white"),
            King("white"), Bishop("white"), Knight("white"), Rook("white")
        ]

    def get_piece(self, row, col):
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def print_board_console(self):
        for r in range(8):
            row_str = ""
            for c in range(8):
                piece = self.grid[r][c]
                if piece:
                    symbol = piece.name[0].upper() if piece.color == "white" else piece.name[0].lower()
                    if piece.name == "knight":
                        symbol = "N" if piece.color == "white" else "n"
                    row_str += f"{symbol} "
                else:
                    row_str += ". "
            print(row_str)