# core/board.py

from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King

from core.move import Move
from core.utils import is_valid_position


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

    def initialize(self):
        """
            Reset chess board to the intial state
        """
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self._setup_standard_board()
    
    def get_piece(self, row, col=None):
        """
            Get the piece at target position
            Support argument as (row, col) or tuple(row, col) from core/rules.py
        """
        if col is None:
            row, col = row

        if is_valid_position(row, col):
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

    def set_piece(self, pos, piece):
        """
            Put a piece into `pos` position (tuple)
            Need for simulating making a move in rules.py
        """
        row, col = pos
        if is_valid_position(row, col):
            self.grid[row][col] = piece

    def move_piece(self, move: Move):
        """
            Make a move, update grid and handle special rules
        """
        piece = self.grid[move.start_row][move.start_col]

        # Move to the target position
        self.grid[move.end_row][move.end_col] = piece
        self.grid[move.start_row][move.start_col] = None

        if piece is not None:
            piece.has_moved = True    # Piece.has_moved

        # --- Handle special rule based on flags from Move ---
        if getattr(move, 'is_castle', False):
            if move.end_col == 6:       # Kingside
                rook = self.grid[move.start_row][7]
                self.grid[move.start_row][5] = rook
                self.grid[move.start_row][7] = None
                if rook: rook.has_moved = True
            elif move.end_col == 2:     # Queenside
                rook = self.grid[move.start_row][0]
                self.grid[move.start_row][3] = rook
                self.grid[move.start_row][0] = None
                if rook: rook.has_moved = True
            
        elif getattr(move, 'is_en_passant', False):
            # Remove the pawn that is made en passant (the same row with start_row)
            self.grid[move.start_row][move.end_col] = None

        elif getattr(move, 'is_promotion', False):
            # Default promote to Queen
            promoted_piece = Queen(piece.color)     # Piece.color
            promoted_piece.has_moved = True
            self.grid[move.end_row][move.end_col] = promoted_piece