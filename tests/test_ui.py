"""
Unit tests for the UI module.
Tests cover BoardUI, PieceUI, InputHandler, and Animation components.
Uses a headless Pygame display (no window shown during tests).
"""
import unittest
import os
import sys
import pygame


# Initialize Pygame in headless mode for testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
# Create a tiny hidden display for Surface operations
pygame.display.set_mode((1, 1))


# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import SQUARE_SIZE, BOARD_WIDTH, BOARD_HEIGHT, ROWS, COLS, BOARD_OFFSET_X, BOARD_OFFSET_Y, PIECE_SIZE, BLACK_ROOK_SIZE
from ui.board_ui import BoardUI
from ui.piece_ui import PieceUI, PIECE_NAME_TO_LETTER
from ui.input_handler import InputHandler
from ui.animation import Animation
from core.board import Board
from core.game_state import GameState


# ==================== Test BoardUI ====================

class TestBoardUI(unittest.TestCase):
    """Tests for the BoardUI class."""

    def setUp(self):
        self.board_ui = BoardUI()

    def test_get_square_from_pos_valid(self):
        """Test conversion from pixel position to board square."""
        # Top-left corner of the grid -> (0, 0)
        sq = BoardUI.get_square_from_pos((BOARD_OFFSET_X + 5, BOARD_OFFSET_Y + 5))
        self.assertEqual(sq, (0, 0))

        # Center of first square
        sq = BoardUI.get_square_from_pos((BOARD_OFFSET_X + SQUARE_SIZE // 2, BOARD_OFFSET_Y + SQUARE_SIZE // 2))
        self.assertEqual(sq, (0, 0))

        # Bottom-right corner of the actual playable board
        sq = BoardUI.get_square_from_pos((BOARD_OFFSET_X + 8*SQUARE_SIZE - 1, BOARD_OFFSET_Y + 8*SQUARE_SIZE - 1))
        self.assertEqual(sq, (7, 7))

    def test_get_square_from_pos_middle(self):
        """Test square detection at row=3, col=4."""
        x = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y = BOARD_OFFSET_Y + 3 * SQUARE_SIZE + SQUARE_SIZE // 2
        sq = BoardUI.get_square_from_pos((x, y))
        self.assertEqual(sq, (3, 4))

    def test_get_square_from_pos_outside(self):
        """Clicking outside the board returns None."""
        self.assertIsNone(BoardUI.get_square_from_pos((-1, 0)))
        self.assertIsNone(BoardUI.get_square_from_pos((BOARD_WIDTH, 0)))
        self.assertIsNone(BoardUI.get_square_from_pos((0, BOARD_HEIGHT)))
        self.assertIsNone(BoardUI.get_square_from_pos((BOARD_WIDTH + 50, 400)))

    def test_get_square_from_pos_all_corners(self):
        """Test all four corners of the playable grid."""
        # Top-left
        self.assertEqual(BoardUI.get_square_from_pos((BOARD_OFFSET_X, BOARD_OFFSET_Y)), (0, 0))
        # Top-right
        self.assertEqual(
            BoardUI.get_square_from_pos((BOARD_OFFSET_X + 8*SQUARE_SIZE - 1, BOARD_OFFSET_Y)),
            (0, 7)
        )
        # Bottom-left
        self.assertEqual(
            BoardUI.get_square_from_pos((BOARD_OFFSET_X, BOARD_OFFSET_Y + 8*SQUARE_SIZE - 1)),
            (7, 0)
        )
        # Bottom-right
        self.assertEqual(
            BoardUI.get_square_from_pos((BOARD_OFFSET_X + 8*SQUARE_SIZE - 1, BOARD_OFFSET_Y + 8*SQUARE_SIZE - 1)),
            (7, 7)
        )

    def test_draw_board_no_crash(self):
        """Ensure draw_board runs without errors."""
        screen = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        self.board_ui.draw_board(screen)  # Should not raise

    def test_draw_highlights_no_crash(self):
        """Ensure draw_highlights runs without errors with various inputs."""
        screen = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        self.board_ui.draw_highlights(screen)
        self.board_ui.draw_highlights(screen, selected_sq=(3, 4))
        self.board_ui.draw_highlights(screen, valid_moves=[(2, 3), (4, 5)])
        self.board_ui.draw_highlights(
            screen,
            last_move={"start": (6, 4), "end": (4, 4)}
        )
        self.board_ui.draw_highlights(screen, king_in_check_pos=(0, 4))


# ==================== Test PieceUI ====================

class TestPieceUI(unittest.TestCase):
    """Tests for the PieceUI class."""

    def setUp(self):
        self.piece_ui = PieceUI()

    def test_piece_name_mapping(self):
        """Verify all standard piece names are mapped."""
        expected = {"pawn", "rook", "knight", "bishop", "queen", "king"}
        self.assertEqual(set(PIECE_NAME_TO_LETTER.keys()), expected)

    def test_knight_maps_to_n(self):
        """Knight should map to 'n', not 'k'."""
        self.assertEqual(PIECE_NAME_TO_LETTER["knight"], "n")

    def test_king_maps_to_k(self):
        """King should map to 'k'."""
        self.assertEqual(PIECE_NAME_TO_LETTER["king"], "k")

    def test_all_images_loaded(self):
        """All 12 piece images (6 types x 2 colors) should be loaded."""
        self.assertEqual(len(self.piece_ui.images), 12)
        for color in ["white", "black"]:
            for piece_name in PIECE_NAME_TO_LETTER:
                key = f"{color}_{piece_name}"
                self.assertIn(key, self.piece_ui.images,
                              f"Missing image for {key}")
                self.assertIsNotNone(self.piece_ui.images[key])

    def test_image_size(self):
        """All piece images should be PIECE_SIZE x PIECE_SIZE (except black_rook)."""
        for key, img in self.piece_ui.images.items():
            expected = BLACK_ROOK_SIZE if key == "black_rook" else PIECE_SIZE
            self.assertEqual(img.get_width(), expected,
                             f"{key} width mismatch")
            self.assertEqual(img.get_height(), expected,
                             f"{key} height mismatch")

    def test_get_image_key(self):
        """Test image key generation from a Piece object."""
        board_obj = Board()
        # White rook at (7, 0)
        rook = board_obj.grid[7][0]
        key = self.piece_ui._get_image_key(rook)
        self.assertEqual(key, "white_rook")

        # Black pawn at (1, 0)
        pawn = board_obj.grid[1][0]
        key = self.piece_ui._get_image_key(pawn)
        self.assertEqual(key, "black_pawn")

    def test_get_piece_image(self):
        """Test that get_piece_image returns a Surface."""
        board_obj = Board()
        piece = board_obj.grid[7][4]  # White king
        img = self.piece_ui.get_piece_image(piece)
        self.assertIsInstance(img, pygame.Surface)

    def test_draw_pieces_no_crash(self):
        """Ensure draw_pieces runs without errors."""
        screen = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        board_obj = Board()
        self.piece_ui.draw_pieces(screen, board_obj.grid)

    def test_draw_pieces_with_skip(self):
        """Ensure draw_pieces with skip_pos runs without errors."""
        screen = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        board_obj = Board()
        self.piece_ui.draw_pieces(screen, board_obj.grid, skip_pos=(6, 0))


# ==================== Test InputHandler ====================

class TestInputHandler(unittest.TestCase):
    """Tests for the InputHandler class."""

    def setUp(self):
        self.handler = InputHandler()
        board_obj = Board()
        self.game_state = GameState(board_obj)

    def test_initial_state(self):
        """Test that InputHandler starts with no selection."""
        self.assertIsNone(self.handler.selected_square)
        self.assertEqual(self.handler.valid_moves, [])
        self.assertFalse(self.handler.dragging)
        self.assertIsNone(self.handler.drag_piece)

    def test_select_own_piece(self):
        """Clicking on a white piece on white's turn should select it."""
        # Simulate clicking on white pawn at (6, 4) -> e2
        x = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y = BOARD_OFFSET_Y + 6 * SQUARE_SIZE + SQUARE_SIZE // 2
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (x, y), "button": 1}
        )
        self.handler.handle_event(event, self.game_state)

        self.assertEqual(self.handler.selected_square, (6, 4))
        self.assertTrue(len(self.handler.valid_moves) > 0)
        # White pawn at e2 can move to e3 and e4
        self.assertIn((5, 4), self.handler.valid_moves)  # e3
        self.assertIn((4, 4), self.handler.valid_moves)  # e4

    def test_select_enemy_piece_no_select(self):
        """Clicking on a black piece on white's turn should not select it."""
        x = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y = BOARD_OFFSET_Y + 1 * SQUARE_SIZE + SQUARE_SIZE // 2
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (x, y), "button": 1}
        )
        self.handler.handle_event(event, self.game_state)

        self.assertIsNone(self.handler.selected_square)

    def test_click_empty_square_no_select(self):
        """Clicking on an empty square with nothing selected does nothing."""
        x = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y = BOARD_OFFSET_Y + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (x, y), "button": 1}
        )
        result = self.handler.handle_event(event, self.game_state)

        self.assertIsNone(self.handler.selected_square)

    def test_deselect_on_click_outside(self):
        """Clicking outside the board should deselect."""
        # First select a piece
        x = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y = BOARD_OFFSET_Y + 6 * SQUARE_SIZE + SQUARE_SIZE // 2
        down_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": 1}
        )
        # Need to mouse up to end drag without moving
        up_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": 1}
        )
        self.handler.handle_event(down_event, self.game_state)
        self.handler.handle_event(up_event, self.game_state)
        self.assertEqual(self.handler.selected_square, (6, 4))

        # Now click outside
        outside_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (BOARD_WIDTH + 50, 400), "button": 1}
        )
        result = self.handler.handle_event(outside_event, self.game_state)
        self.assertIsNone(self.handler.selected_square)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "deselect")

    def test_move_action_returned(self):
        """Selecting a piece and clicking a valid target returns a move action."""
        # Select white pawn at (6, 4)
        x1 = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y1 = BOARD_OFFSET_Y + 6 * SQUARE_SIZE + SQUARE_SIZE // 2
        down_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (x1, y1), "button": 1}
        )
        up_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (x1, y1), "button": 1}
        )
        self.handler.handle_event(down_event, self.game_state)
        self.handler.handle_event(up_event, self.game_state)

        # Click on e4 (valid move)
        x2 = BOARD_OFFSET_X + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        y2 = BOARD_OFFSET_Y + 4 * SQUARE_SIZE + SQUARE_SIZE // 2
        move_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (x2, y2), "button": 1}
        )
        result = self.handler.handle_event(move_event, self.game_state)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "move")
        self.assertEqual(result["start"], (6, 4))
        self.assertEqual(result["end"], (4, 4))

    def test_reset(self):
        """Test that reset clears all state."""
        self.handler.selected_square = (3, 3)
        self.handler.valid_moves = [(2, 3)]
        self.handler.dragging = True

        self.handler.reset()

        self.assertIsNone(self.handler.selected_square)
        self.assertEqual(self.handler.valid_moves, [])
        self.assertFalse(self.handler.dragging)

    def test_is_king_in_check_initial(self):
        """At the start of the game, no king should be in check."""
        pos = self.handler.get_king_in_check_pos(self.game_state)
        self.assertIsNone(pos)


# ==================== Test Animation ====================

class TestAnimation(unittest.TestCase):
    """Tests for the Animation class."""

    def test_initial_state(self):
        """Animation should not be animating initially."""
        anim = Animation()
        self.assertFalse(anim.is_animating())

    def test_animating_flag(self):
        """Test that animating flag can be set."""
        anim = Animation()
        anim.animating = True
        self.assertTrue(anim.is_animating())
        anim.animating = False
        self.assertFalse(anim.is_animating())


# ==================== Test Renderer ====================

class TestRenderer(unittest.TestCase):
    """Smoke tests for the Renderer class."""

    def test_renderer_init_no_crash(self):
        """Renderer should initialize without errors."""
        from ui.renderer import Renderer
        renderer = Renderer()
        self.assertIsNotNone(renderer.board_ui)
        self.assertIsNotNone(renderer.piece_ui)
        self.assertIsNotNone(renderer.animation)

    def test_full_draw_no_crash(self):
        """Full draw call should not crash."""
        from ui.renderer import Renderer
        from config import WINDOW_WIDTH, WINDOW_HEIGHT
        renderer = Renderer()
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        board_obj = Board()
        game_state = GameState(board_obj)
        input_handler = InputHandler()
        renderer.draw(screen, game_state, input_handler)  # Should not raise


if __name__ == "__main__":
    unittest.main()
