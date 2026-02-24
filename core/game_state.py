from core.rules import get_legal_moves, is_checkmate, is_stalemate

class GameState:
    def __init__(self, board_obj):
        self.board_obj = board_obj
        self.board = board_obj.grid 
        self.current_turn = "white"
        self.move_log = []
        self.is_checkmate = False
        self.is_stalemate = False

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
            
            self.board[r2][c2] = piece
            self.board[r1][c1] = None
            piece.has_moved = True

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
        if is_checkmate(self.board, self.current_turn):
            self.is_checkmate = True
        elif is_stalemate(self.board, self.current_turn):
            self.is_stalemate = True