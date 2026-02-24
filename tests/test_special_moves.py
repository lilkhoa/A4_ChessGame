import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from pieces.king import King
from pieces.rook import Rook
from pieces.pawn import Pawn
from pieces.queen import Queen
from core.game_state import GameState

class MockBoard:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]

class TestSpecialMoves(unittest.TestCase):
    def setUp(self):
        self.mock_board = MockBoard()
        self.state = GameState(self.mock_board)

    def test_pawn_promotion(self):
        white_pawn = Pawn("white")
        self.state.board[1][0] = white_pawn
        
        self.state.process_move((1, 0), (0, 0))
        
        promoted_piece = self.state.board[0][0]
        self.assertIsInstance(promoted_piece, Queen)
        self.assertEqual(promoted_piece.color, "white")

    def test_castling_kingside(self):
        white_king = King("white")
        white_rook = Rook("white")
        
        self.state.board[7][4] = white_king
        self.state.board[7][7] = white_rook
        
        self.state.process_move((7, 4), (7, 6))
        
        self.assertIsInstance(self.state.board[7][6], King)
        self.assertIsInstance(self.state.board[7][5], Rook)
        self.assertIsNone(self.state.board[7][4])
        self.assertIsNone(self.state.board[7][7])

    def test_en_passant(self):
        white_pawn = Pawn("white")
        black_pawn = Pawn("black")
        
        self.state.board[3][4] = white_pawn
        self.state.board[1][5] = black_pawn
        self.state.current_turn = "black"
        
        self.state.process_move((1, 5), (3, 5))
        self.state.process_move((3, 4), (2, 5))
        
        self.assertIsInstance(self.state.board[2][5], Pawn)
        self.assertEqual(self.state.board[2][5].color, "white")
        self.assertIsNone(self.state.board[3][5])

if __name__ == "__main__":
    unittest.main()