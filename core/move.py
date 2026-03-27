class Move:
    def __init__(self, start_sq, end_sq, board_grid, is_en_passant=False, is_castle=False, is_promotion=False, promotion_piece=None):

        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        
        self.piece_moved = board_grid[self.start_row][self.start_col]
        self.piece_captured = board_grid[self.end_row][self.end_col]
        
        self.move_id = (self.start_row * 1000) + (self.start_col * 100) + (self.end_row * 10) + (self.end_col)

        # Flags for special move
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.is_promotion = is_promotion
        # Promotion piece identifier, typically one of: 'Q', 'R', 'B', 'N'
        # Can also be a piece class for backwards compatibility.
        self.promotion_piece = promotion_piece

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False
    
    def __str__(self):
        return f"Move({self.start_row},{self.start_col} -> {self.end_row},{self.end_col})"

    @staticmethod
    def _to_algebraic(row, col):
        """Convert board coordinates to algebraic notation."""
        file_char = chr(ord('a') + col)
        rank_char = str(8 - row)
        return f"{file_char}{rank_char}"

    @staticmethod
    def _from_algebraic(square):
        """Convert algebraic notation to board coordinates."""
        file_char = square[0].lower()
        rank_char = square[1]
        col = ord(file_char) - ord('a')
        row = 8 - int(rank_char)
        return row, col

    def to_network_format(self):
        """
        Convert move to compact network format.

        Examples:
            - Normal move: e2e4
            - Promotion: e7e8Q
        """
        src = self._to_algebraic(self.start_row, self.start_col)
        dst = self._to_algebraic(self.end_row, self.end_col)

        promo = ""
        if self.promotion_piece is not None:
            if isinstance(self.promotion_piece, str):
                promo = self.promotion_piece.upper()
            else:
                # Backwards compatibility with piece classes
                name = getattr(self.promotion_piece, "__name__", "")
                promo_map = {
                    "Queen": "Q",
                    "Rook": "R",
                    "Bishop": "B",
                    "Knight": "N",
                }
                promo = promo_map.get(name, "")

        return f"{src}{dst}{promo}"

    @classmethod
    def from_network_format(cls, move_str):
        """
        Parse network move string into structured tuple.

        Returns:
            (start_pos, end_pos, promotion_code)
        """
        if not isinstance(move_str, str) or len(move_str) < 4:
            raise ValueError(f"Invalid move string: {move_str}")

        start_sq = move_str[:2]
        end_sq = move_str[2:4]
        promo = move_str[4].upper() if len(move_str) >= 5 else None

        start_pos = cls._from_algebraic(start_sq)
        end_pos = cls._from_algebraic(end_sq)
        return start_pos, end_pos, promo