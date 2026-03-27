import pygame
from config import SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, COLOR_PANEL_BG, COLOR_ACCENT


PROMOTION_CODES = ["Q", "R", "B", "N"]
PROMOTION_NAMES = {
    "Q": "queen",
    "R": "rook",
    "B": "bishop",
    "N": "knight",
}


class PromotionDialog:
    """Non-blocking promotion chooser popup."""

    def __init__(self, piece_ui):
        self.piece_ui = piece_ui
        self.visible = False
        self.color = "white"
        self.popup_rect = None
        self.choice_rects = []
        self.hover_index = -1

    def open(self, color, col, row, reversed_view=False):
        """Open the promotion popup near the promotion square."""
        self.visible = True
        self.color = color

        display_col = (7 - col) if reversed_view else col
        display_row = (7 - row) if reversed_view else row

        cell_size = int(SQUARE_SIZE)
        dialog_w = cell_size
        dialog_h = cell_size * 4

        # Prefer drawing upward from the target square; clamp into board bounds.
        dialog_x = BOARD_OFFSET_X + int(display_col * SQUARE_SIZE)
        desired_y = BOARD_OFFSET_Y + int(display_row * SQUARE_SIZE) - (dialog_h - cell_size)
        min_y = BOARD_OFFSET_Y
        max_y = BOARD_OFFSET_Y + int(8 * SQUARE_SIZE) - dialog_h
        dialog_y = max(min_y, min(desired_y, max_y))

        self.popup_rect = pygame.Rect(dialog_x - 4, dialog_y - 4, dialog_w + 8, dialog_h + 8)
        self.choice_rects = [
            pygame.Rect(dialog_x, dialog_y + i * cell_size, cell_size, cell_size)
            for i in range(4)
        ]
        self.hover_index = -1

    def close(self):
        self.visible = False
        self.popup_rect = None
        self.choice_rects = []
        self.hover_index = -1

    def draw(self, screen):
        """Draw promotion popup if active."""
        if not self.visible or not self.popup_rect:
            return

        mouse_pos = pygame.mouse.get_pos()
        self.hover_index = -1
        for i, rect in enumerate(self.choice_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_index = i
                break

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, COLOR_PANEL_BG, self.popup_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_ACCENT, self.popup_rect, 2, border_radius=8)

        for i, code in enumerate(PROMOTION_CODES):
            rect = self.choice_rects[i]
            if i == self.hover_index:
                pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=4)
            else:
                pygame.draw.rect(screen, COLOR_PANEL_BG, rect, border_radius=4)

            key = f"{self.color}_{PROMOTION_NAMES[code]}"
            image = self.piece_ui.images.get(key)
            if image:
                img_w, img_h = image.get_size()
                ix = rect.centerx - img_w // 2
                iy = rect.centery - img_h // 2
                screen.blit(image, (ix, iy))

    def get_selected_piece(self, mouse_pos):
        """
        Return selected promotion code on click.

        Returns:
            None: click outside popup or no selection
            str: one of 'Q', 'R', 'B', 'N'
        """
        if not self.visible:
            return None

        for i, rect in enumerate(self.choice_rects):
            if rect.collidepoint(mouse_pos):
                return PROMOTION_CODES[i]
        return None