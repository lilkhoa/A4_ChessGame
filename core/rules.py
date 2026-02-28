from typing import List, Tuple, Optional, Set
from collections import defaultdict


class Rules:
    """
    Central rules engine for chess game validation.
    Handles all chess rule logic including move validation, check, checkmate, and draw detection.
    """
    
    def __init__(self):
        self.position_history = []
        self.move_history = []
        
    def is_legal_move(self, board, move, game_state) -> bool:
        """
        Check if a move is legal according to chess rules.
        
        Args:
            board: The current board state
            move: The move to validate
            game_state: The current game state
            
        Returns:
            bool: True if the move is legal, False otherwise
        """
        piece = board.get_piece(move.start)
        
        # Check if there's a piece at the start position
        if piece is None:
            return False
            
        # Check if it's the correct player's turn
        if piece.color != game_state.current_player:
            return False
            
        # Check if the move follows the piece's movement rules
        valid_moves = piece.get_valid_moves(board, move.start)
        if move.end not in valid_moves:
            return False
            
        # Check if the move would leave the king in check (simulate the move)
        if self._would_leave_king_in_check(board, move, piece.color):
            return False
            
        return True
    
    def get_all_legal_moves(self, board, game_state, color: str) -> List:
        """
        Get all legal moves for a given color.
        
        Args:
            board: The current board state
            game_state: The current game state
            color: The color ('white' or 'black') to get moves for
            
        Returns:
            List: All legal moves for the specified color
        """
        legal_moves = []
        
        # Iterate through all positions on the board
        for row in range(8):
            for col in range(8):
                position = (row, col)
                piece = board.get_piece(position)
                
                if piece is not None and piece.color == color:
                    valid_moves = piece.get_valid_moves(board, position)
                    
                    for end_position in valid_moves:
                        from core.move import Move
                        move = Move(position, end_position)
                        
                        if not self._would_leave_king_in_check(board, move, color):
                            legal_moves.append(move)
        
        return legal_moves
    
    def is_in_check(self, board, color: str) -> bool:
        """
        Check if the king of the specified color is in check.
        
        Args:
            board: The current board state
            color: The color ('white' or 'black') to check
            
        Returns:
            bool: True if the king is in check, False otherwise
        """
        # Find the king's position
        king_position = self._find_king(board, color)
        if king_position is None:
            return False
            
        # Check if any opponent piece can attack the king
        opponent_color = 'black' if color == 'white' else 'white'
        
        # Iterate through all opponent pieces
        for row in range(8):
            for col in range(8):
                position = (row, col)
                piece = board.get_piece(position)
                
                if piece is not None and piece.color == opponent_color:
                    valid_moves = piece.get_valid_moves(board, position)
                    if king_position in valid_moves:
                        return True
        
        return False
    
    def is_checkmate(self, board, game_state, color: str) -> bool:
        """
        Check if the specified color is in checkmate.
        
        Args:
            board: The current board state
            game_state: The current game state
            color: The color ('white' or 'black') to check
            
        Returns:
            bool: True if the color is in checkmate, False otherwise
        """
        if not self.is_in_check(board, color):
            return False   
        legal_moves = self.get_all_legal_moves(board, game_state, color)
        return len(legal_moves) == 0
    
    def is_stalemate(self, board, game_state, color: str) -> bool:
        """
        Check if the specified color is in stalemate.

        Args:
            board: The current board state
            game_state: The current game state
            color: The color ('white' or 'black') to check
            
        Returns:
            bool: True if the color is in stalemate, False otherwise
        """
        if self.is_in_check(board, color):
            return False
        legal_moves = self.get_all_legal_moves(board, game_state, color)
        return len(legal_moves) == 0
    
    def is_insufficient_material(self, board) -> bool:
        """
        Check if there is insufficient material for checkmate.
        
        Insufficient material occurs in these cases:
        1. King vs King
        2. King + Bishop vs King
        3. King + Knight vs King
        4. King + Bishop vs King + Bishop (bishops on same color squares)
        
        Args:
            board: The current board state
            
        Returns:
            bool: True if there's insufficient material, False otherwise
        """
        white_pieces = []
        black_pieces = []
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece((row, col))
                if piece is not None:
                    if piece.color == 'white':
                        white_pieces.append((piece.piece_type, (row, col)))
                    else:
                        black_pieces.append((piece.piece_type, (row, col)))
        
        white_pieces = [(p, pos) for p, pos in white_pieces if p != 'king']
        black_pieces = [(p, pos) for p, pos in black_pieces if p != 'king']
        
        # King vs King
        if len(white_pieces) == 0 and len(black_pieces) == 0:
            return True
        
        # King + Bishop vs King or King vs King + Bishop
        if len(white_pieces) == 1 and len(black_pieces) == 0:
            if white_pieces[0][0] == 'bishop':
                return True
        if len(black_pieces) == 1 and len(white_pieces) == 0:
            if black_pieces[0][0] == 'bishop':
                return True
        
        # King + Knight vs King or King vs King + Knight
        if len(white_pieces) == 1 and len(black_pieces) == 0:
            if white_pieces[0][0] == 'knight':
                return True
        if len(black_pieces) == 1 and len(white_pieces) == 0:
            if black_pieces[0][0] == 'knight':
                return True
        
        # King + Bishop vs King + Bishop (same color squares)
        if len(white_pieces) == 1 and len(black_pieces) == 1:
            if white_pieces[0][0] == 'bishop' and black_pieces[0][0] == 'bishop':
                white_pos = white_pieces[0][1]
                black_pos = black_pieces[0][1]
                white_color = (white_pos[0] + white_pos[1]) % 2
                black_color = (black_pos[0] + black_pos[1]) % 2
                if white_color == black_color:
                    return True
        
        return False
    
    def is_threefold_repetition(self, board) -> bool:
        """
        Check if the current position has occurred three times (3-fold repetition).
        
        Args:
            board: The current board state
            
        Returns:
            bool: True if the position has occurred 3+ times, False otherwise
        """
        current_position = self._get_position_hash(board)
        count = self.position_history.count(current_position)
        return count >= 2
    
    def is_fifty_move_rule(self, game_state) -> bool:
        """
        Check if the 50-move rule applies.
        
        The 50-move rule states that a draw can be claimed if 50 moves
        have been made without a pawn move or capture.
        
        Args:
            game_state: The current game state
            
        Returns:
            bool: True if 50 moves without pawn move/capture, False otherwise
        """
        if hasattr(game_state, 'halfmove_clock'):
            return game_state.halfmove_clock >= 100
        
        return False
    
    def is_draw(self, board, game_state, color: str) -> bool:
        """
        Check if the game is a draw by any means.
        
        Args:
            board: The current board state
            game_state: The current game state
            color: The color whose turn it is
            
        Returns:
            bool: True if the game is a draw, False otherwise
        """
        # Check all draw conditions
        if self.is_stalemate(board, game_state, color):
            return True
            
        if self.is_insufficient_material(board):
            return True
            
        if self.is_threefold_repetition(board):
            return True
            
        if self.is_fifty_move_rule(game_state):
            return True
        
        return False
    
    def update_position_history(self, board):
        """
        Update the position history for threefold repetition detection.
        
        Args:
            board: The current board state
        """
        position_hash = self._get_position_hash(board)
        self.position_history.append(position_hash)
    
    def reset_position_history(self):
        """Reset the position history (for new games)."""
        self.position_history = []
        self.move_history = []


    # ==================== Private Helper Methods ====================
    
    def _would_leave_king_in_check(self, board, move, color: str) -> bool:
        """
        Check if a move would leave the king in check.

        Args:
            board: The current board state
            move: The move to simulate
            color: The color of the player making the move
            
        Returns:
            bool: True if the move would leave the king in check, False otherwise
        """
        # Simulate the move
        original_piece = board.get_piece(move.start)
        captured_piece = board.get_piece(move.end)
        
        # Temporarily make the move
        board.set_piece(move.end, original_piece)
        board.set_piece(move.start, None)
        
        # Check if the king is in check
        in_check = self.is_in_check(board, color)
        
        # Undo the move
        board.set_piece(move.start, original_piece)
        board.set_piece(move.end, captured_piece)
        
        return in_check
    
    def _find_king(self, board, color: str) -> Optional[Tuple[int, int]]:
        """
        Find the position of the king for the specified color.
        
        Args:
            board: The current board state
            color: The color ('white' or 'black') of the king to find
            
        Returns:
            Optional[Tuple[int, int]]: The position of the king, or None if not found
        """
        for row in range(8):
            for col in range(8):
                position = (row, col)
                piece = board.get_piece(position)
                
                if piece is not None and piece.color == color and piece.piece_type == 'king':
                    return position
        
        return None
    
    def _get_position_hash(self, board) -> str:
        """
        Generate a hash of the current board position.
        
        Args:
            board: The current board state
            
        Returns:
            str: A hash representing the current position
        """
        position_str = ""
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece((row, col))
                if piece is None:
                    position_str += "."
                else:
                    position_str += piece.color[0] + piece.piece_type[0]
        
        return position_str
    
    def filter_legal_moves(self, board, game_state, moves: List, color: str) -> List:
        """
        Filter a list of moves to only include legal moves.
        
        This removes moves that would leave the king in check.
        
        Args:
            board: The current board state
            game_state: The current game state
            moves: List of moves to filter
            color: The color of the player
            
        Returns:
            List: Filtered list of legal moves
        """
        legal_moves = []
        
        for move in moves:
            if not self._would_leave_king_in_check(board, move, color):
                legal_moves.append(move)
        
        return legal_moves


# ==================== Standalone Helper Functions ====================
# These are used by game_state.py and tests, which import them as free functions.
# They operate on the raw board grid (2D list of Piece/None), NOT the Board object.

def _find_king_on_grid(board_grid, color):
    """Find the king's position on a raw board grid."""
    for r in range(8):
        for c in range(8):
            p = board_grid[r][c]
            if p and p.name == "king" and p.color == color:
                return (r, c)
    return None


def is_in_check(board_grid, color):
    """
    Check if the king of the given color is in check.

    Args:
        board_grid: 8x8 list-of-lists of Piece or None
        color: 'white' or 'black'

    Returns:
        bool
    """
    king_pos = _find_king_on_grid(board_grid, color)
    if king_pos is None:
        return False

    opponent = "black" if color == "white" else "white"
    for r in range(8):
        for c in range(8):
            p = board_grid[r][c]
            if p and p.color == opponent:
                try:
                    attacks = p.get_valid_moves(board_grid, r, c, None)
                except TypeError:
                    attacks = p.get_valid_moves(board_grid, r, c)
                if king_pos in attacks:
                    return True
    return False


def get_legal_moves(board_grid, piece, row, col, last_move=None):
    """
    Get all legal moves for a piece, filtering out moves that leave the king in check.

    Args:
        board_grid: 8x8 list-of-lists
        piece: The Piece object to move
        row, col: Current position of the piece
        last_move: The last move dict (for en passant), or None

    Returns:
        list of (row, col) tuples
    """
    # Get raw valid moves from the piece
    try:
        raw_moves = piece.get_valid_moves(board_grid, row, col, last_move)
    except TypeError:
        raw_moves = piece.get_valid_moves(board_grid, row, col)

    legal = []
    for (er, ec) in raw_moves:
        # Simulate the move
        original = board_grid[row][col]
        captured = board_grid[er][ec]

        # Handle en passant capture simulation
        ep_captured = None
        if piece.name == "pawn" and col != ec and board_grid[er][ec] is None:
            ep_captured = board_grid[row][ec]
            board_grid[row][ec] = None

        board_grid[er][ec] = original
        board_grid[row][col] = None

        if not is_in_check(board_grid, piece.color):
            legal.append((er, ec))

        # Undo
        board_grid[row][col] = original
        board_grid[er][ec] = captured
        if ep_captured is not None:
            board_grid[row][ec] = ep_captured

    return legal


def is_checkmate(board_grid, color, last_move=None):
    """
    Check if the given color is in checkmate.

    Args:
        board_grid: 8x8 list-of-lists
        color: 'white' or 'black'
        last_move: Last move dict or None

    Returns:
        bool
    """
    if not is_in_check(board_grid, color):
        return False

    # Check if any piece of the given color has a legal move
    for r in range(8):
        for c in range(8):
            p = board_grid[r][c]
            if p and p.color == color:
                if get_legal_moves(board_grid, p, r, c, last_move):
                    return False
    return True


def is_stalemate(board_grid, color, last_move=None):
    """
    Check if the given color is in stalemate.

    Args:
        board_grid: 8x8 list-of-lists
        color: 'white' or 'black'
        last_move: Last move dict or None

    Returns:
        bool
    """
    if is_in_check(board_grid, color):
        return False

    for r in range(8):
        for c in range(8):
            p = board_grid[r][c]
            if p and p.color == color:
                if get_legal_moves(board_grid, p, r, c, last_move):
                    return False
    return True
