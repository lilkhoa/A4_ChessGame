import pygame
import os
from config import (
    BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, BOARD_WIDTH, BOARD_HEIGHT,
    COLOR_LIGHT_SQUARE, COLOR_DARK_SQUARE,
    COLOR_SELECTED, COLOR_VALID_MOVE, COLOR_LAST_MOVE, COLOR_CHECK,
    BOARD_IMAGE_PATH
)


class BoardUI:
    """Handles rendering of the chess board, coordinates, and visual highlights."""

    def __init__(self):
        self.board_image = None
        self.board_image_reversed = None
        self._load_board_image()

    def _load_board_image(self):
        """Load and scale the board background image."""
        try:
            if os.path.exists(BOARD_IMAGE_PATH):
                raw = pygame.image.load(BOARD_IMAGE_PATH).convert()
                self.board_image = pygame.transform.smoothscale(raw, (BOARD_WIDTH, BOARD_HEIGHT))
            
            # Load reversed board image
            reversed_path = os.path.join(os.path.dirname(BOARD_IMAGE_PATH), "chess-board-reversed.png")
            if os.path.exists(reversed_path):
                raw_reversed = pygame.image.load(reversed_path).convert()
                self.board_image_reversed = pygame.transform.smoothscale(raw_reversed, (BOARD_WIDTH, BOARD_HEIGHT))
        except pygame.error as e:
            print(f"Warning: Could not load board image: {e}")
            self.board_image = None
            self.board_image_reversed = None



    def draw_board(self, screen, reversed_view=False):
        """
        Draw the chess board background.
        
        Args:
            screen: Pygame display surface
            reversed_view: If True, use the reversed board image (for black player perspective)
        """
        board_to_draw = self.board_image_reversed if reversed_view and self.board_image_reversed else self.board_image
        
        if board_to_draw:
            screen.blit(board_to_draw, (0, 0))
        else:
            self._draw_fallback_board(screen, reversed_view)

    def _draw_fallback_board(self, screen, reversed_view=False):
        """
        Draw a simple colored board if the image is not available.
        
        Args:
            screen: Pygame display surface
            reversed_view: If True, reverse the board colors for black player perspective
        """
        # Note: Fallback draws from top-left, matching logical coordinates
        for row in range(8):
            for col in range(8):
                # When reversed, flip the color pattern
                if reversed_view:
                    color = COLOR_DARK_SQUARE if (row + col) % 2 == 0 else COLOR_LIGHT_SQUARE
                else:
                    color = COLOR_LIGHT_SQUARE if (row + col) % 2 == 0 else COLOR_DARK_SQUARE
                x = BOARD_OFFSET_X + int(col * SQUARE_SIZE)
                y = BOARD_OFFSET_Y + int(row * SQUARE_SIZE)
                size = int(SQUARE_SIZE) + 1 # +1 to prevent 1px gaps
                rect = pygame.Rect(x, y, size, size)
                pygame.draw.rect(screen, color, rect)


    def draw_highlights(self, screen, selected_sq=None, valid_moves=None,
                        last_move=None, king_in_check_pos=None, board_grid=None, reversed_view=False):
        """
        Draw all visual highlights on the board.

        Args:
            selected_sq: (row, col) of the currently selected square
            valid_moves: list of (row, col) tuples for valid target squares
            last_move: dict with 'start' and 'end' keys for the last move
            king_in_check_pos: (row, col) of king in check, if any
            reversed_view: If True, flip coordinates for black player perspective
        """
        # Highlight the last move (start and end squares)
        if last_move:
            for pos in [last_move.get("start"), last_move.get("end")]:
                if pos:
                    self._draw_square_highlight(screen, pos, COLOR_LAST_MOVE, reversed_view)

        # Highlight selected square
        if selected_sq:
            self._draw_square_highlight(screen, selected_sq, COLOR_SELECTED, reversed_view)

        # Valid move dots
        if valid_moves:
            for pos in valid_moves:
                is_capture = False
                if board_grid:
                    r, c = pos
                    if board_grid[r][c] is not None:
                        is_capture = True
                self._draw_valid_move_indicator(screen, pos, is_capture, reversed_view)

        # Highlight king in check
        if king_in_check_pos:
            self._draw_square_highlight(screen, king_in_check_pos, COLOR_CHECK, reversed_view)

    def _draw_square_highlight(self, screen, pos, color, reversed_view=False):
        """Draw a semi-transparent highlight on a square."""
        row, col = pos
        size = int(SQUARE_SIZE) + 1
        highlight_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        highlight_surface.fill(color)
        # Flip coordinates when board is reversed
        display_col = (7 - col) if reversed_view else col
        display_row = (7 - row) if reversed_view else row
        x = BOARD_OFFSET_X + int(display_col * SQUARE_SIZE)
        y = BOARD_OFFSET_Y + int(display_row * SQUARE_SIZE)
        screen.blit(highlight_surface, (x, y))

    def _draw_valid_move_indicator(self, screen, pos, is_capture=False, reversed_view=False):
        """Draw a circle indicator for a valid move target."""
        row, col = pos
        size = int(SQUARE_SIZE)
        # Flip coordinates when board is reversed
        display_col = (7 - col) if reversed_view else col
        display_row = (7 - row) if reversed_view else row

        indicator = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if is_capture:
            # Draw a vivid red ring for capture moves
            pygame.draw.circle(
                indicator,
                (230, 60, 60, 200),
                (size // 2, size // 2),
                int(size * 0.45),
                int(size * 0.1)  # ring thickness
            )
        else:
            # Draw standard green dot
            pygame.draw.circle(
                indicator,
                COLOR_VALID_MOVE,
                (size // 2, size // 2),
                size // 6
            )
            
        x = BOARD_OFFSET_X + int(display_col * SQUARE_SIZE)
        y = BOARD_OFFSET_Y + int(display_row * SQUARE_SIZE)
        screen.blit(indicator, (x, y))

    @staticmethod
    def get_square_from_pos(mouse_pos, reversed_view=False):
        """
        Convert a pixel position to board coordinates.

        Args:
            mouse_pos: (x, y) pixel position
            reversed_view: If True, flip coordinates for black player perspective

        Returns:
            (row, col) tuple, or None if outside the board
        """
        x, y = mouse_pos
        # Adjust for board borders
        grid_x = x - BOARD_OFFSET_X
        grid_y = y - BOARD_OFFSET_Y
        
        # Check if the click is actually within the 8x8 playable area
        grid_limit = 8 * SQUARE_SIZE
        if 0 <= grid_x < grid_limit and 0 <= grid_y < grid_limit:
            col = int(grid_x / SQUARE_SIZE)
            row = int(grid_y / SQUARE_SIZE)
            # Flip coordinates when board is reversed
            if reversed_view:
                col = 7 - col
                row = 7 - row
            return (row, col)
        return None
