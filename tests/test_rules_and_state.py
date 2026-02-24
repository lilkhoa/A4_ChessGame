import unittest
from pieces.king import King
from pieces.rook import Rook
from core.rules import is_in_check, is_checkmate, is_stalemate
from core.game_state import GameState

class MockBoard:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]

class TestRulesAndState(unittest.TestCase):
    def setUp(self):
        self.mock_board = MockBoard()
        self.state = GameState(self.mock_board)

    def test_check_and_checkmate(self):
        white_king = King("white")
        black_rook1 = Rook("black")
        black_rook2 = Rook("black")

        self.state.board[0][0] = white_king
        self.state.board[0][7] = black_rook1
        self.state.board[1][7] = black_rook2

        self.assertTrue(is_in_check(self.state.board, "white"))
        self.assertTrue(is_checkmate(self.state.board, "white"))
        self.assertFalse(is_stalemate(self.state.board, "white"))

    def test_stalemate(self):
        white_king = King("white")
        black_rook1 = Rook("black")
        black_rook2 = Rook("black")

        self.state.board[0][0] = white_king
        self.state.board[1][7] = black_rook1
        self.state.board[7][1] = black_rook2

        self.assertFalse(is_in_check(self.state.board, "white"))
        self.assertFalse(is_checkmate(self.state.board, "white"))
        self.assertTrue(is_stalemate(self.state.board, "white"))

    def test_process_move(self):
        white_rook = Rook("white")
        black_rook = Rook("black")
        
        self.state.board[7][0] = white_rook
        self.state.board[0][0] = black_rook
        
        success = self.state.process_move((7, 0), (0, 0))
        
        self.assertTrue(success)
        self.assertEqual(self.state.current_turn, "black")
        self.assertIsNone(self.state.board[7][0])
        self.assertEqual(self.state.board[0][0], white_rook)
        self.assertEqual(len(self.state.move_log), 1)

if __name__ == "__main__":
    unittest.main()