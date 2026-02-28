# tests/test_board.py
import sys
import unittest

sys.path.append(".")

from core.board import Board
from core.move import Move
from core.game_state import GameState

from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King

class TestBoardAndGameState(unittest.TestCase):
    def setUp(self):
        """
            Called before each test case.
        """
        self.board = Board()
        self.game_state = GameState(self.board)

    def clear_board(self):
        """
            Helper function: Clear the board to re-setup special chess state
        """
        self.board.grid = [[None for _ in range(8)] for _ in range(8)]

    def test_board_initialization(self):
        """
            Check whether board initialization is correct
        """
        # Check Block Rook at (0,0)
        piece = self.board.get_piece(0,0)
        self.assertIsNotNone(piece)
        self.assertEqual(piece.name, "rook")
        self.assertEqual(piece.color, "black")

        # Check the empty cell at the center of board (4,4)
        empty_square = self.board.get_piece(4,4)
        self.assertIsNone(empty_square)

    def test_basic_pawn_move(self):
        """
            Check the move of the White Pawn
        """
        start_pos = (6, 4)      # White pawn E col
        end_pos = (4, 4)        # Go straight 2 squares

        # Take GameState to process_move
        success = self.game_state.process_move(start_pos, end_pos)

        self.assertTrue(success, "Valid move must return True")
        self.assertIsNone(self.board.get_piece(6,4), "Old square must be empty")

        moved_piece = self.board.get_piece(4, 4)
        self.assertIsNotNone(moved_piece, "Must be a Pawn at new square (4,4)")
        self.assertEqual(moved_piece.name, "pawn")
        self.assertEqual(self.game_state.current_turn, "black", "Must be the Black's turn")

    def test_en_passant(self):
        """
            Check the en passant logic
        """
        self.clear_board()
        # Setup: White has Pawn at e5 (3, 4), Black has Pawn at d7 (1, 3)
        self.board.set_piece((3, 4), Pawn("white"))
        self.board.set_piece((1, 3), Pawn("black"))
        
        # Turn 1: Black move Pawn d7 to d5 (double step)
        self.game_state.current_turn = "black"
        self.game_state.process_move((1, 3), (3, 3))
        
        # Turn 2: White take a en passant move d5 by going diagonally to d6 (2, 3)
        # Because this is the White turn, current_turn must be 'white'
        success = self.game_state.process_move((3, 4), (2, 3))
        
        self.assertTrue(success, "The en passant move must be valid")
        self.assertEqual(self.board.get_piece(2, 3).name, "pawn", "White Pawn must be placed at d6")
        self.assertIsNone(self.board.get_piece(3, 3), "Black Pawn at d5 must be removed (successful en passant move)")

    def test_castling_kingside(self):
        """
            Check the Kingside Castling move logic.
        """
        self.clear_board()
        # Setup: Just let the White King and Rook, the middle line has to be clean
        self.board.set_piece((7, 4), King("white"))
        self.board.set_piece((7, 7), Rook("white"))
        self.game_state.current_turn = "white"
        
        # White take a Kingside Castling move (King moves from e1 to g1)
        success = self.game_state.process_move((7, 4), (7, 6))
        
        self.assertTrue(success, "Castling move must be valid")
        self.assertEqual(self.board.get_piece(7, 6).name, "king", "King must move to g1")
        self.assertEqual(self.board.get_piece(7, 5).name, "rook", "Rook must jump to f1")
        self.assertIsNone(self.board.get_piece(7, 7), "Original square of Rook must be empty")

    def test_promotion(self):
        """
            Check the Queen Promotion logic
        """
        self.clear_board()
        # Setup: White Pawn at row 7 (prepare to promote)
        self.board.set_piece((1, 0), Pawn("white"))
        self.game_state.current_turn = "white"
        
        # Move White Pawn to row 8
        success = self.game_state.process_move((1, 0), (0, 0))
        
        self.assertTrue(success, "Promotion move must be valid")
        promoted_piece = self.board.get_piece(0, 0)
        self.assertIsNotNone(promoted_piece)
        self.assertEqual(promoted_piece.name, "queen", "Pawn must promote to Queen")

    def test_move_equality_and_id(self):
        """K
            Check the ID generation and compare 2 moves of class Move
        """
        # Move from (6,4) to (4,4)
        move1 = Move((6, 4), (4, 4), self.board.grid)
        move2 = Move((6, 4), (4, 4), self.board.grid)
        # Another move: from (6,4) to (5,4)
        move3 = Move((6, 4), (5, 4), self.board.grid)
        
        self.assertEqual(move1, move2, "Two objects Move have the same coordinate must be equal")
        self.assertNotEqual(move1, move3, "Two objects Move have two different coordinates must be different")
        # Check the ID: start_row(6)*1000 + start_col(4)*100 + end_row(4)*10 + end_col(4) = 6444
        self.assertEqual(move1.move_id, 6444, "Move ID incorrect computation")

if __name__ == "__main__":
    unittest.main()  