# core/game_state.py


from core.rules import Rules
from core.board import Board
from core.move import Move

from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King

class GameState:
    def __init__(self, board_obj, rules=None):

        self.board_obj = board_obj
        self.board = board_obj.grid
        
        # Use shared Rules engine or create new one
        self.rules = rules if rules is not None else Rules() 

        self.current_turn = "white"
        self.move_log = []

        self.is_checkmate = False
        self.is_draw = False
        self.draw_reason = None
        self.timeout_winner = None

        self.white_time = 300.0
        self.black_time = 300.0

        self.halfmove_clock = 0
        
        # For AI integration
        self.pending_ai_move = None

    @property
    def is_game_over(self):
        """
            Check whether game is over
        """
        return self.is_checkmate or self.is_draw or self.timeout_winner is not None

    def process_move(self, start_pos, end_pos, promotion_piece=None):
        """
            Handle move: Check valid -> Make a move -> Update game state
            
            Args:
                start_pos: (row, col) starting position
                end_pos: (row, col) ending position
                promotion_piece: Optional piece class for pawn promotion (Queen, Rook, Bishop, Knight)
        """
        r1, c1 = start_pos
        r2, c2 = end_pos
        piece = self.board[r1][c1]

        if not piece or piece.color != self.current_turn:
            return False

        last_move = self.move_log[-1] if self.move_log else None
        legal_moves = self.rules.get_legal_moves_for_piece(self.board_obj, piece, r1, c1, last_move)
        
        if end_pos in legal_moves:

            move = Move(start_pos, end_pos, self.board)

            if piece.name == "pawn" and c1 != c2 and self.board[r2][c2] is None:
                move.is_en_passant = True
            elif piece.name == "king" and abs(c2-c1) == 2:
                move.is_castle = True
            elif piece.name == "pawn" and (r2 == 0 or r2 == 7):
                move.is_promotion = True
                move.promotion_piece = promotion_piece
            
            # Check whether a piece is captured (include en passant move)
            is_capture = (move.piece_captured is not None) or move.is_en_passant
            is_pawn_move = (piece.name == "pawn")

            self.board_obj.move_piece(move)

            if is_pawn_move or is_capture:
                self.halfmove_clock = 0
            else:
                self.halfmove_clock += 1


            self.move_log.append({
                "piece": piece,
                "start": start_pos,
                "end": end_pos,
                "captured": move.piece_captured
            })

            # Don't switch turn here - let turn_controller handle it
            # self.current_turn will be switched by turn_controller.complete_turn()
            return True
            
        return False

    def check_game_over(self):
        """
            Check and update game over flag
            Note: This checks the CURRENT player (after turn switch)
        """
        # Check for checkmate
        if self.rules.is_checkmate(self.board_obj, self, self.current_turn):
            self.is_checkmate = True
        # Check for draw (includes stalemate, 50-move rule, insufficient material, 3-fold repetition)
        elif self.rules.is_draw(self.board_obj, self, self.current_turn):
            self.is_draw = True