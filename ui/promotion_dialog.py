import pygame
from config import (
    SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    COLOR_BG, COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_ACCENT, COLOR_BORDER
)
from pieces.queen import Queen
from pieces.rook import Rook
from pieces.bishop import Bishop
from pieces.knight import Knight


PROMOTION_CHOICES = [
    {"class": Queen, "name": "queen"},
    {"class": Rook, "name": "rook"},
    {"class": Bishop, "name": "bishop"},
    {"class": Knight, "name": "knight"},
]


class PromotionDialog:
    """
    Displays a popup dialog for the player to choose which piece
    to promote a pawn to (Queen, Rook, Bishop, or Knight).
    """

    def __init__(self, piece_ui):
        """
        Args:
            piece_ui: PieceUI instance to get piece images from.
        """
        self.piece_ui = piece_ui

    def show(self, screen, clock, color, col, reversed_view=False):
        """
        Show the promotion dialog and block until the player makes a choice.

        Args:
            screen: Pygame display surface
            clock: Pygame clock
            color: 'white' or 'black' — the color of the promoting pawn
            col: Column (0-7) where the pawn promotes, used for positioning
            reversed_view: If True, flip column for black perspective

        Returns:
            Piece class (Queen, Rook, Bishop, or Knight)
        """
        # Calculate dialog position near the promotion column
        display_col = (7 - col) if reversed_view else col
        dialog_x = BOARD_OFFSET_X + int(display_col * SQUARE_SIZE)
        
        # For white promoting (row 0), show dialog from top; for black (row 7), from bottom
        if color == "white":
            start_row = 0 if not reversed_view else 4
        else:
            start_row = 4 if not reversed_view else 0
        
        dialog_y = BOARD_OFFSET_Y + int(start_row * SQUARE_SIZE)
        
        cell_size = int(SQUARE_SIZE)
        dialog_w = cell_size
        dialog_h = cell_size * 4

        # Build rects for each choice
        choice_rects = []
        for i in range(4):
            rect = pygame.Rect(dialog_x, dialog_y + i * cell_size, cell_size, cell_size)
            choice_rects.append(rect)

        hover_index = -1

        while True:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, rect in enumerate(choice_rects):
                        if rect.collidepoint(event.pos):
                            return PROMOTION_CHOICES[i]["class"]

            # Update hover
            hover_index = -1
            for i, rect in enumerate(choice_rects):
                if rect.collidepoint(mouse_pos):
                    hover_index = i

            # Draw semi-transparent overlay over the whole screen
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            # Draw panel background
            panel_rect = pygame.Rect(dialog_x - 4, dialog_y - 4, dialog_w + 8, dialog_h + 8)
            pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_ACCENT, panel_rect, 2, border_radius=8)

            # Draw each piece option
            for i, choice in enumerate(PROMOTION_CHOICES):
                rect = choice_rects[i]
                
                # Highlight on hover
                if i == hover_index:
                    pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=4)
                else:
                    pygame.draw.rect(screen, COLOR_PANEL_BG, rect, border_radius=4)

                # Get piece image
                key = f"{color}_{choice['name']}"
                image = self.piece_ui.images.get(key)
                if image:
                    # Center the image in the cell
                    img_w, img_h = image.get_size()
                    ix = rect.centerx - img_w // 2
                    iy = rect.centery - img_h // 2
                    screen.blit(image, (ix, iy))

            pygame.display.flip()
            clock.tick(60)
