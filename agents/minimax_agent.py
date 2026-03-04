import math
from .base_agent import BaseAgent
from core.board import Board
from core.game_state import GameState
from core.move import Move


class MinimaxAgent(BaseAgent):
    """
    Minimax agent with alpha-beta pruning and position evaluation.
    
    This agent uses:
    - Minimax algorithm with alpha-beta pruning for efficient search
    - Piece-square tables for positional evaluation
    - Material counting with piece values
    - Transposition table for caching evaluated positions
    """
    
    def __init__(self, name="MinimaxAgent", depth=3):
        super().__init__(name)
        self.depth = depth
        
        # Piece-square tables (PST) for positional evaluation
        # Index: row * 8 + col (0-63)
        self.PST = {
            'pawn': [
                0,   0,   0,   0,   0,   0,   0,   0,
                10,  20,  20, -10, -10,  20,  20,  10,
                5,  10,  15,  25,  25,  15,  10,   5,
                0,   5,  10,  30,  30,  10,   5,   0,
                5,  10,  15,  20,  20,  15,  10,   5,
                5,   5,  10,  15,  15,  10,   5,   5,
                2,   2,   2,   2,   2,   2,   2,   2,
                0,   0,   0,   0,   0,   0,   0,   0
            ],
            'knight': [
                -50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50,
            ],
            'bishop': [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10, 10,  0,  0,  0,  0, 10,-10,
                -10,  0, 15, 20, 20, 15,  0,-10,
                -10, 10, 20, 25, 25, 20, 10,-10,
                -10, 10, 20, 25, 25, 20, 10,-10,
                -10,  0, 15, 20, 20, 15,  0,-10,
                -10,  5,  0, 10, 10,  0,  5,-10,
                -20,-10,-10,-10,-10,-10,-10,-20
            ],
            'rook': [
                0,  0,  0,  0,  0,  0,  0,  0,
                -5,-5, -5, -5, -5, -5, -5, -5,
                -10,-10, -5, -5, -5, -5,-10,-10,
                -10,-10, -5, 10, 10, -5,-10,-10,
                -5,  0,  0, 20, 20,  0,  0, -5,
                0,  5, 10, 20, 20, 10,  5,  0,
                10, 15, 15, 20, 20, 15, 15, 10,
                0,  0,  0,  5,  5,  0,  0,  0
            ],
            'queen': [
                -20,-10,-10, -5, -5,-10,-10,-20,
                -10,-20,-20,-10,-10,-20,-20,-10,
                -10,-20,-10, -5, -5,-10,-20,-10,
                -5,-10, -5,  0,  0, -5,-10, -5,
                -5,-10, -5,  0,  0, -5,-10, -5,
                -10,-20,-10, -5, -5,-10,-20,-10,
                -10,-20,-20,-10,-10,-20,-20,-10,
                -20,-10,-10, -5, -5,-10,-10,-20
            ]
        }
        
        # Transposition table for caching positions
        self.TT = {}
        
        # Store previous board state for repetition detection
        self.previous_position_hash = None
    
    def get_move(self, board: Board, game_state: GameState, color: str) -> Move:
        """
        Get the best move using minimax with alpha-beta pruning.
        
        Args:
            board: Current board state
            game_state: Current game state
            color: Color this agent is playing ('white' or 'black')
            
        Returns:
            Best move found, or None if no legal moves
        """
        legal_moves = self.get_legal_moves(board, game_state, color)
        
        if not legal_moves:
            return None
        
        best_move = None
        best_value = -math.inf if color == 'white' else math.inf
        
        # Get position hash from 2 moves ago for repetition detection
        position_hash_two_ago = None
        if len(game_state.move_log) >= 2:
            position_hash_two_ago = self._get_position_hash_from_history(
                board, game_state.move_log[:-2]
            )
        
        # Evaluate each legal move
        ordered_moves = self._order_moves(board, game_state, legal_moves)
        
        for move in ordered_moves:
            # Simulate the move
            sim_board, sim_state = self._simulate_move(board, game_state, move, color)
            
            # Run minimax on resulting position
            board_value = self._minimax(
                sim_board, sim_state, 
                self._opposite_color(color),
                self.depth - 1, 
                -math.inf, math.inf
            )
            
            # Penalize moves that repeat position from 2 moves ago
            current_hash = self._get_position_hash(sim_board, sim_state)
            if position_hash_two_ago and current_hash == position_hash_two_ago:
                board_value += -2000 if color == 'white' else 2000
            
            # Select best move based on color
            if color == 'white':
                if board_value > best_value:
                    best_value = board_value
                    best_move = move
            else:
                if board_value < best_value:
                    best_value = board_value
                    best_move = move
        
        # Store current position for future repetition detection
        self.previous_position_hash = self._get_position_hash(board, game_state)
        
        return best_move
    
    def _order_moves(self, board: Board, game_state: GameState, legal_moves: list) -> list:
        """
        Order moves for better alpha-beta pruning efficiency.
        Prioritizes: captures > promotions > other moves
        """
        def move_score(move):
            score = 0
            
            # Prioritize captures
            if move.piece_captured is not None:
                # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                victim_value = self._get_piece_value(move.piece_captured.name)
                attacker_value = self._get_piece_value(move.piece_moved.name)
                score += 10 + victim_value - attacker_value
            
            # Prioritize promotions
            if hasattr(move, 'is_promotion') and move.is_promotion:
                score += 10 + 9  # Queen value
            
            return score
        
        sorted_moves = sorted(legal_moves, key=lambda m: move_score(m), reverse=True)
        return sorted_moves
    
    def _minimax(self, board: Board, game_state: GameState, color: str, 
                 depth: int, alpha: float, beta: float) -> float:
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            board: Current board state
            game_state: Current game state
            color: Current player's color
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            
        Returns:
            Evaluation score for the position
        """
        # Terminal conditions
        if depth == 0 or self._is_game_over(board, game_state, color):
            return self._evaluate_board(board, game_state, color)
        
        # Check transposition table
        position_hash = self._get_position_hash(board, game_state)
        if position_hash in self.TT:
            entry = self.TT[position_hash]
            if entry["depth"] >= depth:
                return entry["value"]
        
        # Get legal moves
        legal_moves = self.get_legal_moves(board, game_state, color)
        ordered_moves = self._order_moves(board, game_state, legal_moves)
        
        if color == 'white':
            # Maximizing player
            max_eval = -math.inf
            for move in ordered_moves:
                sim_board, sim_state = self._simulate_move(board, game_state, move, color)
                eval_score = self._minimax(
                    sim_board, sim_state, 
                    self._opposite_color(color),
                    depth - 1, alpha, beta
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            self.TT[position_hash] = {"depth": depth, "value": max_eval}
            return max_eval
        
        else:
            # Minimizing player
            min_eval = math.inf
            for move in ordered_moves:
                sim_board, sim_state = self._simulate_move(board, game_state, move, color)
                eval_score = self._minimax(
                    sim_board, sim_state,
                    self._opposite_color(color),
                    depth - 1, alpha, beta
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            self.TT[position_hash] = {"depth": depth, "value": min_eval}
            return min_eval
        
    def _evaluate_board(self, board: Board, game_state: GameState, color: str) -> float:
        """
        Evaluate the board position from white's perspective.
        Positive = good for white, Negative = good for black
        
        Considers:
        - Material value (pieces)
        - Piece-square tables (positional value)
        - Opening phase bonuses
        - Check status
        - Terminal conditions (checkmate, stalemate)
        """
        # Check terminal states first
        if self.rules.is_checkmate(board, game_state, 'white'):
            return -999999
        if self.rules.is_checkmate(board, game_state, 'black'):
            return 999999
        if self.rules.is_stalemate(board, game_state, color):
            return 0
        
        # Piece base values
        piece_values = {
            'pawn': 1000,
            'knight': 3000,
            'bishop': 3200,
            'rook': 5000,
            'queen': 9000,
            'king': 6000,
        }
        
        # Check if in opening phase (first 15 moves)
        move_number = len(game_state.move_log) // 2 + 1
        opening_phase = move_number <= 15
        
        score = 0
        
        # Evaluate all pieces on board
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece is None:
                    continue
                
                # Base material value
                base_value = piece_values.get(piece.name, 0)
                
                # Piece-square table bonus
                pst_bonus = 0
                if piece.name in self.PST:
                    # Calculate square index
                    if piece.color == 'white':
                        idx = row * 8 + col
                    else:
                        # Mirror for black (flip vertically)
                        idx = (7 - row) * 8 + col
                    
                    pst_bonus = self.PST[piece.name][idx]
                    
                    # Stronger PST effect in opening
                    if opening_phase:
                        pst_bonus *= 3
                    else:
                        pst_bonus *= 1.2
                
                piece_score = base_value + pst_bonus
                
                # Add to score (positive for white, negative for black)
                if piece.color == 'white':
                    score += piece_score
                else:
                    score -= piece_score
        
        # Opening phase bonuses
        if opening_phase:
            score += self._evaluate_opening_position(board)
        
        # Check bonus/penalty
        if self.rules.is_in_check(board, 'white'):
            score -= 1000
        if self.rules.is_in_check(board, 'black'):
            score += 1000
        
        # Repetition penalty
        current_hash = self._get_position_hash(board, game_state)
        if self.previous_position_hash and current_hash == self.previous_position_hash:
            # Penalize returning to previous position
            score += -2000 if game_state.current_turn == 'white' else 2000
        
        return score

    def _evaluate_opening_position(self, board: Board) -> float:
        """
        Evaluate position-specific bonuses for the opening phase.
        Returns a score adjustment (positive for white advantage).
        """
        score = 0
        
        # 1. Pawn center control bonus (e4, d4, e5, d5)
        center_squares = [(4, 4), (4, 3), (3, 4), (3, 3)]  # e4, d4, e5, d5
        for row, col in center_squares:
            piece = board.get_piece(row, col)
            if piece and piece.name == 'pawn':
                score += 40 if piece.color == 'white' else -40
        
        # 2. Knight development to good squares
        knight_good_squares = [
            (5, 2), (6, 3), (6, 4), (5, 5),  # c3, d2, e2, f3 for white
            (2, 2), (1, 3), (1, 4), (2, 5),  # c6, d7, e7, f6 for black
        ]
        for row, col in knight_good_squares:
            piece = board.get_piece(row, col)
            if piece and piece.name == 'knight':
                score += 30 if piece.color == 'white' else -30
        
        # 3. Bishop on long diagonals
        long_diagonals = [
            (5, 0), (6, 1), (7, 2),  # a3, b2, c1 for white
            (4, 5), (3, 6), (2, 7),  # f4, g5, h6
            (2, 0), (1, 1), (0, 2),  # a6, b7, c8 for black
            (3, 5), (4, 6), (5, 7),  # f5, g4, h3
        ]
        for row, col in long_diagonals:
            piece = board.get_piece(row, col)
            if piece and piece.name == 'bishop':
                score += 40 if piece.color == 'white' else -40
        
        # 4. Rooks should stay on back rank in opening
        # White rooks at a1(7,0) h1(7,7), Black rooks at a8(0,0) h8(0,7)
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece and piece.name == 'rook':
                    if piece.color == 'white':
                        if row != 7 or (col != 0 and col != 7):
                            score -= 40  # Penalty for early rook movement
                    else:
                        if row != 0 or (col != 0 and col != 7):
                            score += 40
        
        # 5. Queen early development penalty (in center)
        queen_center_penalty = [(5, 3), (5, 4), (4, 3), (4, 4)]  # d3, e3, d4, e4
        for row, col in queen_center_penalty:
            piece = board.get_piece(row, col)
            if piece and piece.name == 'queen':
                score -= 60 if piece.color == 'white' else 60
        
        return score
    
    # ============================================================================
    # Helper Methods for Board State Management
    # ============================================================================
    
    def _simulate_move(self, board: Board, game_state: GameState, 
                      move: Move, color: str) -> tuple:
        """
        Create a deep copy of board and game_state, then apply the move.
        Returns (new_board, new_game_state) without modifying originals.
        """
        # Deep copy board
        new_board = Board()
        new_board.grid = [[None for _ in range(8)] for _ in range(8)]
        
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    # Create new piece instance
                    new_piece = self._copy_piece(piece)
                    new_board.grid[row][col] = new_piece
        
        # Deep copy game state
        new_state = GameState(new_board, rules=game_state.rules)
        new_state.current_turn = self._opposite_color(color)  # Will be switched after move
        new_state.halfmove_clock = game_state.halfmove_clock
        new_state.move_log = list(game_state.move_log)  # Shallow copy is fine
        
        # Apply the move to the new board
        new_board.move_piece(move)
        
        # Update halfmove clock
        is_capture = move.piece_captured is not None or getattr(move, 'is_en_passant', False)
        is_pawn_move = move.piece_moved and move.piece_moved.name == 'pawn'
        if is_pawn_move or is_capture:
            new_state.halfmove_clock = 0
        else:
            new_state.halfmove_clock += 1
        
        # Switch turn in simulated state
        new_state.current_turn = self._opposite_color(color)
        
        return new_board, new_state
    
    def _copy_piece(self, piece):
        """Create a deep copy of a piece."""
        piece_class = type(piece)
        new_piece = piece_class(piece.color)
        new_piece.has_moved = piece.has_moved
        return new_piece
    
    def _get_position_hash(self, board: Board, game_state: GameState) -> str:
        """
        Generate a unique string hash for the current position.
        Similar to FEN but simpler.
        """
        hash_parts = []
        
        # Board position
        for row in range(8):
            row_str = ""
            empty_count = 0
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    # Use first letter, uppercase for white, lowercase for black
                    symbol = piece.name[0]
                    if piece.name == 'knight':
                        symbol = 'n'
                    row_str += symbol.upper() if piece.color == 'white' else symbol.lower()
            if empty_count > 0:
                row_str += str(empty_count)
            hash_parts.append(row_str)
        
        # Turn and halfmove clock
        hash_parts.append(game_state.current_turn[0])  # 'w' or 'b'
        hash_parts.append(str(game_state.halfmove_clock))
        
        return '/'.join(hash_parts)
    
    def _get_position_hash_from_history(self, board: Board, move_log_subset: list) -> str:
        """
        Get position hash by reconstructing from move history.
        Used to detect repetitions.
        """
        # For simplicity, return None if complex reconstruction is needed
        # This is a simplified implementation
        return None
    
    def _is_game_over(self, board: Board, game_state: GameState, color: str) -> bool:
        """Check if the game is over (checkmate, stalemate, or draw)."""
        if self.rules.is_checkmate(board, game_state, color):
            return True
        if self.rules.is_stalemate(board, game_state, color):
            return True
        if self.rules.is_draw(board, game_state, color):
            return True
        return False
    
    def _opposite_color(self, color: str) -> str:
        """Return the opposite color."""
        return 'black' if color == 'white' else 'white'
    
    def _get_piece_value(self, piece_name: str) -> int:
        """Get the base material value of a piece."""
        values = {
            'pawn': 1,
            'knight': 3,
            'bishop': 3,
            'rook': 5,
            'queen': 9,
            'king': 100,
        }
        return values.get(piece_name, 0)
    
    def reset(self):
        """Reset agent state for a new game."""
        super().reset()
        self.TT = {}
        self.previous_position_hash = None
