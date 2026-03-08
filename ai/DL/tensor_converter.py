import json
import numpy as np
import csv
import os

from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King


class TensorConverter:
    def __init__(self):
        pass 

    def _parse_fen(self, fen: str):
        """
        Parse a FEN string and return a Board object and GameState object.
        
        FEN format: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        Parts: piece_placement active_color castling en_passant halfmove fullmove
        
        :param fen: FEN notation string
        :return: Tuple of (Board, GameState, en_passant_square_tuple_or_None)
        """
        parts = fen.strip().split()
        if len(parts) < 4:
            raise ValueError(f"Invalid FEN string: {fen}")
        
        piece_placement = parts[0]
        active_color = parts[1]
        castling = parts[2]
        en_passant = parts[3]
        halfmove = int(parts[4]) if len(parts) > 4 else 0
        
        # Create empty board
        board_obj = Board()
        board_obj.grid = [[None for _ in range(8)] for _ in range(8)]
        
        # Parse piece placement
        piece_map = {
            'P': lambda: Pawn('white'), 'N': lambda: Knight('white'), 'B': lambda: Bishop('white'),
            'R': lambda: Rook('white'), 'Q': lambda: Queen('white'), 'K': lambda: King('white'),
            'p': lambda: Pawn('black'), 'n': lambda: Knight('black'), 'b': lambda: Bishop('black'),
            'r': lambda: Rook('black'), 'q': lambda: Queen('black'), 'k': lambda: King('black'),
        }
        
        rows = piece_placement.split('/')
        for row_idx, row_str in enumerate(rows):
            col_idx = 0
            for char in row_str:
                if char.isdigit():
                    col_idx += int(char)  # Skip empty squares
                else:
                    piece = piece_map[char]()
                    board_obj.grid[row_idx][col_idx] = piece
                    col_idx += 1
        
        # Parse castling rights - set has_moved based on castling availability
        # If castling is available, the king and corresponding rook have NOT moved
        white_king = board_obj.grid[7][4]
        black_king = board_obj.grid[0][4]
        white_rook_k = board_obj.grid[7][7]
        white_rook_q = board_obj.grid[7][0]
        black_rook_k = board_obj.grid[0][7]
        black_rook_q = board_obj.grid[0][0]
        
        # Default: pieces have moved (no castling rights)
        if white_king and white_king.name == 'king':
            white_king.has_moved = 'K' not in castling and 'Q' not in castling
        if black_king and black_king.name == 'king':
            black_king.has_moved = 'k' not in castling and 'q' not in castling
        if white_rook_k and white_rook_k.name == 'rook':
            white_rook_k.has_moved = 'K' not in castling
        if white_rook_q and white_rook_q.name == 'rook':
            white_rook_q.has_moved = 'Q' not in castling
        if black_rook_k and black_rook_k.name == 'rook':
            black_rook_k.has_moved = 'k' not in castling
        if black_rook_q and black_rook_q.name == 'rook':
            black_rook_q.has_moved = 'q' not in castling
        
        # Create game state
        rules = Rules()
        game_state = GameState(board_obj, rules)
        game_state.current_turn = 'white' if active_color == 'w' else 'black'
        game_state.halfmove_clock = halfmove
        
        # Parse en passant square
        en_passant_square = None
        if en_passant != '-':
            col = ord(en_passant[0]) - ord('a')
            row = 8 - int(en_passant[1])  # Convert to 0-indexed from top
            en_passant_square = (row, col)
        
        return board_obj, game_state, en_passant_square

    def fen_to_tensor(self, fen: str) -> np.ndarray:
        """
        Convert a FEN string to a 21-channel (8, 8, 21) tensor representation.
        
        :param fen: FEN notation string.
        :return: Numpy array of shape (8, 8, 21).
        """
        board_obj, game_state, en_passant_square = self._parse_fen(fen)
        board = board_obj.grid
        tensor = np.zeros((8, 8, 21), dtype=np.float32)
        
        # Part 1: 12 Piece Position Channels (channel 0-11).
        # Order: white P,N,B,R,Q,K then black P,N,B,R,Q,K
        piece_name_to_idx = {
            'pawn': 0, 'knight': 1, 'bishop': 2, 'rook': 3, 'queen': 4, 'king': 5
        }
        
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece is not None:
                    piece_type_idx = piece_name_to_idx[piece.name]
                    if piece.color == 'white':
                        channel = piece_type_idx
                    else:
                        channel = piece_type_idx + 6
                    
                    tensor[row, col, channel] = 1.0

        # Part 2: 6 Game State Channels (channel 12-17).
        # Channel 12: Turn (1.0 for White's turn, 0.0 for Black's turn).
        if game_state.current_turn == 'white':
            tensor[:, :, 12] = 1.0
        else:
            tensor[:, :, 12] = 0.0
        
        # Castling rights: check has_moved on kings and rooks
        white_king = board[7][4]
        black_king = board[0][4]
        white_rook_k = board[7][7]
        white_rook_q = board[7][0]
        black_rook_k = board[0][7]
        black_rook_q = board[0][0]
        
        # Channel 13: White Kingside Castling Right.
        if (white_king and white_king.name == 'king' and not white_king.has_moved and
            white_rook_k and white_rook_k.name == 'rook' and not white_rook_k.has_moved):
            tensor[:, :, 13] = 1.0
        
        # Channel 14: White Queenside Castling Right.
        if (white_king and white_king.name == 'king' and not white_king.has_moved and
            white_rook_q and white_rook_q.name == 'rook' and not white_rook_q.has_moved):
            tensor[:, :, 14] = 1.0
        
        # Channel 15: Black Kingside Castling Right.
        if (black_king and black_king.name == 'king' and not black_king.has_moved and
            black_rook_k and black_rook_k.name == 'rook' and not black_rook_k.has_moved):
            tensor[:, :, 15] = 1.0
        
        # Channel 16: Black Queenside Castling Right.
        if (black_king and black_king.name == 'king' and not black_king.has_moved and
            black_rook_q and black_rook_q.name == 'rook' and not black_rook_q.has_moved):
            tensor[:, :, 16] = 1.0
        
        # Channel 17: En Passant Square.
        if en_passant_square is not None:
            ep_row, ep_col = en_passant_square
            tensor[ep_row, ep_col, 17] = 1.0
        
        # Part 3: 3 Attack/Control Channels (channel 18-20).
        # Channel 18: White Attack Map (squares attacked/controlled by white pieces).
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece is not None and piece.color == 'white':
                    try:
                        valid_moves = piece.get_valid_moves(board, row, col, None)
                    except TypeError:
                        valid_moves = piece.get_valid_moves(board, row, col)
                    
                    for (target_row, target_col) in valid_moves:
                        tensor[target_row, target_col, 18] = 1.0
        
        # Channel 19: Black Attack Map (squares attacked/controlled by black pieces).
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece is not None and piece.color == 'black':
                    try:
                        valid_moves = piece.get_valid_moves(board, row, col, None)
                    except TypeError:
                        valid_moves = piece.get_valid_moves(board, row, col)
                    
                    for (target_row, target_col) in valid_moves:
                        tensor[target_row, target_col, 19] = 1.0
        
        # Channel 20: Legal Move Squares for Current Player.
        legal_moves = game_state.rules.get_all_legal_moves(board_obj, game_state, game_state.current_turn)
        for move in legal_moves:
            tensor[move.end_row, move.end_col, 20] = 1.0
        
        return tensor

    def convert(self, file_path):
        """
        Loads a dataset and creates tensors for value-only training (ML + Minimax).
        
        :param file_path: Path to data file
        :return: Tuple of (x_boards, y_values) for value-only training.
        """
        return self._convert_csv_format(file_path)
    
    def _convert_csv_format(self, file_path):
        """
        Convert CSV format with FEN and evaluation score.
        
        CSV format: fen_string,evaluation_score
        Example: "r1b2rk1/pp1n2pp/1qn1p3/3pP3/1b1P4/3B1N2/PP1BN1PP/R2QK2R w KQ - 1 13,+248"
        
        :param file_path: Path to the CSV file
        :return: Tuple of (x_boards, y_values) for value-only training
        """
        board_tensors = []
        value_tensors = []
        num_data = 0
        MAX_SAMPLES = 800000
        
        print(f"Loading CSV data from {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for row_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                if num_data == MAX_SAMPLES:
                    print(f"Reached maximum sample limit of {MAX_SAMPLES}. Stopping data loading.")
                    break
                    
                try:
                    # Split on the last comma to handle FEN strings with commas
                    parts = line.rsplit(',', 1)
                    if len(parts) != 2:
                        print(f"Warning: Skipping malformed row {row_idx + 1}: {line}")
                        continue
                    
                    fen_string = parts[0].strip()
                    eval_str = parts[1].strip()
                    
                    # Parse evaluation score
                    # Regular evaluations: +248, -150, +0
                    # Mate scores: #+6 (mate in 6), #-9 (mated in 9)
                    if eval_str.startswith('#'):
                        mate_str = eval_str[1:]
                        mate_moves = float(mate_str.replace('+', ''))
                        
                        # Convert mate scores to large but bounded values  
                        if mate_moves > 0:
                            eval_score = 2000  # Large positive for mate (will be clipped to +15)
                        else:
                            eval_score = -2000  # Large negative for getting mated (will be clipped to -15)
                    else:
                        eval_score = float(eval_str.replace('+', ''))
                    
                    board_tensor = self.fen_to_tensor(fen_string)
                    board_tensors.append(board_tensor)
                    
                    # Convert centipawn to pawn units with clipping
                    # Convert centipawn to pawn units (150cp → 1.5 pawns)
                    pawn_eval = eval_score / 100.0
                    
                    # Clip to prevent extreme values that hurt training
                    normalized_eval = np.clip(pawn_eval, -15.0, 15.0)
                    value_tensors.append([normalized_eval])
                    num_data += 1
                    
                except (ValueError, IndexError) as e:
                    print(f"Warning: Skipping invalid row {row_idx + 1}: {e}")
                    continue
        
        if not board_tensors:
            raise ValueError("No valid data found in CSV file")
        
        x_boards = np.stack(board_tensors, axis=0)      # Shape: (N, 8, 8, 21)
        y_values = np.array(value_tensors, dtype=np.float32)  # Shape: (N, 1)
        
        print(f"Loaded {len(board_tensors)} samples from CSV")
        print(f"Board tensor shape: {x_boards.shape}")
        print(f"Value tensor shape: {y_values.shape}")
        print(f"Value range: [{y_values.min():.3f}, {y_values.max():.3f}]")
        
        return x_boards, y_values
    
    def convert_for_prediction(self, fen: str):
        """
        Convert a board from FEN notation to a tensor for prediction.
        
        :param fen: The FEN notation of the board.
        :return: Board tensor of shape (1, 8, 8, 21) ready for prediction.
        """
        board_tensor = self.fen_to_tensor(fen)
        board_tensor = np.expand_dims(board_tensor, axis=0)
        return board_tensor