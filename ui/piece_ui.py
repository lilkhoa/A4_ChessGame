import pygame
import os
from config import SQUARE_SIZE, PIECE_IMAGE_DIR, BOARD_OFFSET_X, BOARD_OFFSET_Y, PIECE_SIZE, BLACK_ROOK_SIZE


# Mapping from piece.name to image filename letter
PIECE_NAME_TO_LETTER = {
    "pawn": "p",
    "rook": "r",
    "knight": "n",
    "bishop": "b",
    "queen": "q",
    "king": "k",
}


class PieceUI:
    """Handles loading and rendering chess piece images."""

    def __init__(self):
        self.images = {}
        self._load_images()

    def _load_images(self):
        """Load all 12 piece images and scale them to SQUARE_SIZE."""
        for color_prefix, color_name in [("w", "white"), ("b", "black")]:
            for piece_name, letter in PIECE_NAME_TO_LETTER.items():
                key = f"{color_name}_{piece_name}"
                filename = f"{color_prefix}_{letter}.png"
                filepath = os.path.join(PIECE_IMAGE_DIR, filename)
                try:
                    raw = pygame.image.load(filepath).convert_alpha()
                    size = BLACK_ROOK_SIZE if key == "black_rook" else PIECE_SIZE
                    self.images[key] = pygame.transform.smoothscale(
                        raw, (size, size)
                    )
                except (pygame.error, FileNotFoundError) as e:
                    print(f"Warning: Could not load piece image '{filepath}': {e}")
                    self.images[key] = self._create_fallback_image(color_name, letter)

    def _create_fallback_image(self, color_name, letter):
        """Create a simple text-based fallback if image loading fails."""
        # Create a surface of PIECE_SIZE for the fallback
        surface = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
        font = pygame.font.Font(None, PIECE_SIZE // 2) # Font size relative to PIECE_SIZE
        text_color = (255, 255, 255) if color_name == "white" else (30, 30, 30)
        text = font.render(letter.upper(), True, text_color)
        text_rect = text.get_rect(center=(PIECE_SIZE // 2, PIECE_SIZE // 2))

        # Draw a circle background
        bg_color = (200, 200, 200) if color_name == "white" else (80, 80, 80)
        pygame.draw.circle(surface, bg_color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 3)
        surface.blit(text, text_rect)
        return surface

    def _get_image_key(self, piece):
        """
        Get the image dictionary key for a piece.

        Args:
            piece: A Piece object with .color and .name attributes

        Returns:
            str: key like 'white_king', 'black_pawn', etc.
        """
        return f"{piece.color}_{piece.name}"

    def get_piece_image(self, piece):
        """
        Get the Pygame surface for a piece.

        Args:
            piece: A Piece object

        Returns:
            pygame.Surface or None
        """
        key = self._get_image_key(piece)
        return self.images.get(key)

    def draw_pieces(self, screen, board_grid, skip_pos=None, reversed_view=False):
        """
        Draw all pieces on the board.

        Args:
            screen: Pygame display surface
            board_grid: 8x8 grid (list of lists) of Piece or None
            skip_pos: Optional (row, col) to skip (for dragging)
            reversed_view: If True, flip coordinates for black player perspective
        """
        for row in range(8):
            for col in range(8):
                if skip_pos and (row, col) == skip_pos:
                    continue
                piece = board_grid[row][col]
                if piece:
                    image = self.get_piece_image(piece)
                    if image:
                        img_size = image.get_width()
                        offset = int((SQUARE_SIZE - img_size) / 2)
                        # Flip coordinates when board is reversed
                        display_col = (7 - col) if reversed_view else col
                        display_row = (7 - row) if reversed_view else row
                        x = BOARD_OFFSET_X + int(display_col * SQUARE_SIZE) + offset
                        y = BOARD_OFFSET_Y + int(display_row * SQUARE_SIZE) + offset
                        screen.blit(image, (x, y))

    def draw_piece_at(self, screen, piece, pos):
        """
        Draw a single piece at an arbitrary pixel position (for dragging/animation).

        Args:
            screen: Pygame display surface
            piece: A Piece object
            pos: (x, y) pixel position — the piece is centered on this point
        """
        image = self.get_piece_image(piece)
        if image:
            img_size = image.get_width()
            x = pos[0] - img_size // 2
            y = pos[1] - img_size // 2
            screen.blit(image, (x, y))

    def draw_piece_at_square(self, screen, piece, row, col):
        """
        Draw a single piece at a specific board square.

        Args:
            screen: Pygame display surface
            piece: A Piece object
            row, col: Board coordinates
        """
        image = self.get_piece_image(piece)
        if image:
            img_size = image.get_width()
            offset = int((SQUARE_SIZE - img_size) / 2)
            x = BOARD_OFFSET_X + int(col * SQUARE_SIZE) + offset
            y = BOARD_OFFSET_Y + int(row * SQUARE_SIZE) + offset
            screen.blit(image, (x, y))
    
    def get_small_piece_sprite(self, piece_name, color):
        """
        Get a small piece sprite for captured pieces display.
        
        Args:
            piece_name: Name of the piece (e.g., 'pawn', 'queen')
            color: Color of the piece ('white' or 'black')
            
        Returns:
            pygame.Surface or None
        """
        key = f"{color}_{piece_name}"
        return self.images.get(key)
