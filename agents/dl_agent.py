import numpy as np
import os
import random
import copy
from typing import Optional

from .base_agent import BaseAgent
from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from core.move import Move
from ai.DL.our_model import OurModel
from ai.DL.tensor_converter import TensorConverter

class DLAgent(BaseAgent):
    """
    Pure ML + Beam Search chess agent that uses neural network evaluation
    at EVERY depth level for completely ML-driven decision making.
    
    Strategy: ML evaluates all moves at each depth → Select top K → Continue search
    No handcrafted heuristics - pure Stockfish-trained knowledge
    """
    
    def __init__(self, model_path: Optional[str] = None, max_depth: int = 4, beam_width: int = 5, name: str = "DL Agent"):
        """
        Initialize the Pure ML + Beam Search agent.
        
        :param model_path: Path to pre-trained model file (.keras)
        :param max_depth: Maximum search depth (default: 4, efficient with beam search)
        :param beam_width: Number of top moves to explore at each depth (default: 5)
        :param name: Agent name for display
        """
        super().__init__(name=name)
        
        self.max_depth = max_depth
        self.beam_width = beam_width
        
        # Load the trained neural network model
        self.model = OurModel()
        if model_path and os.path.exists(model_path):
            try:
                self.model.load(model_path)
                print(f"Loaded pre-trained model from {model_path}")
            except Exception as e:
                print(f"Failed to load model from {model_path}: {e}")
                print("Using randomly initialized model")
        else:
            print("No model path provided or file not found. Using randomly initialized model")
        
        # Initialize tensor converter for position evaluation
        self.converter = TensorConverter()

    def _board_to_fen(self, board: Board, game_state: GameState) -> str:
        """
        Convert custom Board and GameState to FEN notation.
        
        :param board: Current board object
        :param game_state: Current game state
        :return: FEN string representation
        """
        # Piece placement
        piece_map = {
            ('pawn', 'white'): 'P', ('knight', 'white'): 'N', ('bishop', 'white'): 'B',
            ('rook', 'white'): 'R', ('queen', 'white'): 'Q', ('king', 'white'): 'K',
            ('pawn', 'black'): 'p', ('knight', 'black'): 'n', ('bishop', 'black'): 'b',
            ('rook', 'black'): 'r', ('queen', 'black'): 'q', ('king', 'black'): 'k',
        }
        
        rows = []
        for row in range(8):
            row_str = ""
            empty_count = 0
            for col in range(8):
                piece = board.grid[row][col]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += piece_map[(piece.name, piece.color)]
            if empty_count > 0:
                row_str += str(empty_count)
            rows.append(row_str)
        
        placement = '/'.join(rows)
        
        # Active color
        active_color = 'w' if game_state.current_turn == 'white' else 'b'
        
        # Castling rights
        castling = ""
        white_king = board.grid[7][4]
        black_king = board.grid[0][4]
        white_rook_k = board.grid[7][7]
        white_rook_q = board.grid[7][0]
        black_rook_k = board.grid[0][7]
        black_rook_q = board.grid[0][0]
        
        if white_king and white_king.name == 'king' and not white_king.has_moved:
            if white_rook_k and white_rook_k.name == 'rook' and not white_rook_k.has_moved:
                castling += 'K'
            if white_rook_q and white_rook_q.name == 'rook' and not white_rook_q.has_moved:
                castling += 'Q'
        
        if black_king and black_king.name == 'king' and not black_king.has_moved:
            if black_rook_k and black_rook_k.name == 'rook' and not black_rook_k.has_moved:
                castling += 'k'
            if black_rook_q and black_rook_q.name == 'rook' and not black_rook_q.has_moved:
                castling += 'q'
        
        if not castling:
            castling = '-'
        
        # En passant (simplified - detect from last move)
        en_passant = '-'
        if game_state.move_log:
            last_move = game_state.move_log[-1]
            if last_move['piece'].name == 'pawn':
                start_row, start_col = last_move['start']
                end_row, end_col = last_move['end']
                if abs(end_row - start_row) == 2:
                    ep_row = (start_row + end_row) // 2
                    ep_col = end_col
                    en_passant = chr(ord('a') + ep_col) + str(8 - ep_row)
        
        # Halfmove clock and fullmove number
        halfmove = game_state.halfmove_clock
        fullmove = len(game_state.move_log) // 2 + 1
        
        return f"{placement} {active_color} {castling} {en_passant} {halfmove} {fullmove}"

    def _evaluate_position_ml(self, board: Board, game_state: GameState) -> float:
        """
        Evaluate the board position using the ML model.
        
        :param board: Current board object
        :param game_state: Current game state
        :return: Material evaluation in pawn units (e.g., +3.5 = 3.5 pawn advantage)
        """
        fen = self._board_to_fen(board, game_state)
        board_tensor = self.converter.fen_to_tensor(fen)
        board_tensor = np.expand_dims(board_tensor, axis=0)  # Shape: (1, 8, 8, 21)
        
        try:
            value_pred = self.model.model({'board_input': board_tensor}, training=False)
        except (ValueError, TypeError):
            value_pred = self.model.model(board_tensor, training=False)
        
        if hasattr(value_pred, 'numpy'):
            eval_score = float(value_pred.numpy()[0][0])
        else:
            eval_score = float(value_pred[0][0])
        
        return eval_score
    
    def _evaluate_terminal_ml(self, board: Board, game_state: GameState, is_maximizing: bool) -> float:
        """
        Evaluate terminal positions using ML model.
        
        :param board: Current board object
        :param game_state: Current game state
        :param is_maximizing: Whether the current player is maximizing (White)
        :return: Evaluation score
        """
        if self.rules.is_checkmate(board, game_state, game_state.current_turn):
            # Use large values that exceed any possible model output (±15)
            return -1000.0 if is_maximizing else 1000.0
        elif self.rules.is_stalemate(board, game_state, game_state.current_turn):
            return 0.0
        else:
            return self._evaluate_position_ml(board, game_state)

    def get_move(self, board: Board, game_state: GameState, color: str) -> Move:
        """
        Get the best move using Pure ML + Beam Search strategy.
        
        Uses ML evaluation at EVERY depth level - no handcrafted heuristics.
        Explores only the top beam_width moves at each depth for efficiency.
        
        :param board: Current board object
        :param game_state: Current game state
        :param color: Color this agent is playing ('white' or 'black')
        :return: Selected move
        """
        legal_moves = self.rules.get_all_legal_moves(board, game_state, color)
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # IMMEDIATE CHECKMATE DETECTION: Check all moves for instant mate
        for move in legal_moves:
            temp_board = copy.deepcopy(board)
            temp_game_state = copy.deepcopy(game_state)
            temp_board.move_piece(move)
            temp_game_state.current_turn = 'black' if color == 'white' else 'white'
            
            if self.rules.is_checkmate(temp_board, temp_game_state, temp_game_state.current_turn):
                print(f"Checkmate found! Playing {move}")
                return move
        
        # PURE ML BEAM SEARCH: ML evaluation at every depth
        best_move, best_score = self.beam_search(board, game_state, self.max_depth, color == 'white')
        
        return best_move if best_move else random.choice(legal_moves)

    def beam_search(self, board: Board, game_state: GameState, depth: int, is_maximizing_root: bool) -> tuple:
        """
        Pure ML Beam Search algorithm.
        Uses ML evaluation at EVERY depth level, no heuristics.
        
        :param board: Current board object
        :param game_state: Current game state
        :param depth: Remaining search depth
        :param is_maximizing_root: Whether root player is maximizing (White)
        :return: Tuple of (best_move, best_score)
        """
        legal_moves = self.rules.get_all_legal_moves(board, game_state, game_state.current_turn)
        if not legal_moves:
            return None, self._evaluate_terminal_ml(board, game_state, is_maximizing_root)
        
        if depth == 0:
            # Terminal depth: evaluate with ML
            return None, self._evaluate_position_ml(board, game_state)
        
        # Get top beam_width moves using ML evaluation
        top_moves = self._get_top_moves_beam(board, game_state, legal_moves, game_state.current_turn == 'white')
        
        best_move = None
        best_score = float('-inf') if game_state.current_turn == 'white' else float('inf')
        
        for move in top_moves:
            temp_board = copy.deepcopy(board)
            temp_game_state = copy.deepcopy(game_state)
            temp_board.move_piece(move)
            temp_game_state.current_turn = 'black' if game_state.current_turn == 'white' else 'white'
            
            # Recursive beam search at next depth
            _, score = self.beam_search(temp_board, temp_game_state, depth - 1, is_maximizing_root)
            
            # Min/Max logic based on current player
            if game_state.current_turn == 'white':  # White maximizes
                if score > best_score:
                    best_score = score
                    best_move = move
            else:  # Black minimizes
                if score < best_score:
                    best_score = score
                    best_move = move
        
        return best_move, best_score

    def _get_top_moves_beam(self, board: Board, game_state: GameState, legal_moves: list, is_white_turn: bool) -> list:
        """
        Pure ML move filtering for beam search.
        Selects top beam_width moves based on ML evaluation.
        
        :param board: Current board object
        :param game_state: Current game state
        :param legal_moves: List of all legal moves
        :param is_white_turn: Whether it's White's turn
        :return: Top beam_width moves filtered by pure ML evaluation
        """
        if len(legal_moves) <= self.beam_width:
            return legal_moves
        
        try:
            # Create batch of board positions after each move
            batch_tensors = []
            move_list = []
            
            for move in legal_moves:
                temp_board = copy.deepcopy(board)
                temp_game_state = copy.deepcopy(game_state)
                temp_board.move_piece(move)
                temp_game_state.current_turn = 'black' if game_state.current_turn == 'white' else 'white'
                
                # Convert board state to tensor
                fen = self._board_to_fen(temp_board, temp_game_state)
                board_tensor = self.converter.fen_to_tensor(fen)
                batch_tensors.append(board_tensor)
                move_list.append(move)
            
            # Stack tensors into batch
            batch_array = np.stack(batch_tensors, axis=0)
            
            # PURE ML EVALUATION - batch prediction
            try:
                evaluations = self.model.model({'board_input': batch_array}, training=False)
            except (ValueError, TypeError):
                evaluations = self.model.model(batch_array, training=False)
            
            # Extract ML evaluations and pair with moves
            move_scores = []
            for i, move in enumerate(move_list):
                if hasattr(evaluations, 'numpy'):
                    ml_score = float(evaluations.numpy()[i][0])
                else:
                    ml_score = float(evaluations[i][0])
                
                move_scores.append((move, ml_score))
            
            # PURE ML SELECTION: Choose moves based on player perspective
            if is_white_turn:
                # White wants moves leading to scores closest to +1
                move_scores.sort(key=lambda x: x[1], reverse=True)
            else:
                # Black wants moves leading to scores closest to -1
                move_scores.sort(key=lambda x: x[1], reverse=False)
            
            top_moves = [move for move, _ in move_scores[:self.beam_width]]
            
            return top_moves
            
        except Exception as e:
            print(f"Pure ML filtering failed: {e}, using all moves")
            return legal_moves[:self.beam_width]

    def reset(self):
        """Reset the agent for a new game."""
        super().reset()

    def get_evaluation(self, board: Board, game_state: GameState) -> float:
        """
        Get the pure ML evaluation of a position.
        
        :param board: Board object
        :param game_state: Game state object
        :return: Pure ML material evaluation (pawn units, e.g., +3.5)
        """
        return self._evaluate_position_ml(board, game_state)

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"MLAgent(Pure ML + Beam Search: depth={self.max_depth}, beam_width={self.beam_width})"