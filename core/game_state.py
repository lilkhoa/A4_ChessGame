from core.rules import get_legal_moves, is_checkmate, is_stalemate
from pieces.queen import Queen

class GameState:
    def __init__(self, board_obj):
        self.board_obj = board_obj
        self.board = board_obj.grid 
        self.current_turn = "white"
        self.move_log = []
        self.is_checkmate = False
        self.is_stalemate = False
        self.white_time = 300.0  # 5 minutes in seconds
        self.black_time = 300.0
        self.timeout_winner = None

    @property
    def is_game_over(self):
        return self.is_checkmate or self.is_stalemate or self.timeout_winner is not None

    def process_move(self, start_pos, end_pos):
        r1, c1 = start_pos
        r2, c2 = end_pos
        piece = self.board[r1][c1]

        if not piece or piece.color != self.current_turn:
            return False

        last_move = self.move_log[-1] if self.move_log else None
        legal_moves = get_legal_moves(self.board, piece, r1, c1, last_move)
        
        if end_pos in legal_moves:
            captured_piece = self.board[r2][c2]
            
            if piece.name == "pawn" and c1 != c2 and self.board[r2][c2] is None:
                captured_piece = self.board[r1][c2]
                self.board[r1][c2] = None

            if piece.name == "king" and abs(c2 - c1) == 2:
                if c2 == 6:
                    rook = self.board[r1][7]
                    self.board[r1][5] = rook
                    self.board[r1][7] = None
                    rook.has_moved = True
                elif c2 == 2:
                    rook = self.board[r1][0]
                    self.board[r1][3] = rook
                    self.board[r1][0] = None
                    rook.has_moved = True

            self.board[r2][c2] = piece
            self.board[r1][c1] = None
            piece.has_moved = True

            if piece.name == "pawn" and (r2 == 0 or r2 == 7):
                promoted_piece = Queen(piece.color)
                promoted_piece.has_moved = True
                self.board[r2][c2] = promoted_piece

            self.move_log.append({
                "piece": piece,
                "start": start_pos,
                "end": end_pos,
                "captured": captured_piece
            })

            self.current_turn = "black" if self.current_turn == "white" else "white"
            self.check_game_over()
            return True
            
        return False

    def check_game_over(self):
        last_move = self.move_log[-1] if self.move_log else None
        if is_checkmate(self.board, self.current_turn, last_move):
            self.is_checkmate = True
        elif is_stalemate(self.board, self.current_turn, last_move):
            self.is_stalemate = True