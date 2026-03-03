# ui/pause_menu.py

import pygame
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_PANEL_BG, COLOR_BORDER
)


class PauseMenu:
    """
    In-game pause overlay with Resume / Save & Quit options.
    Drawn on top of the game board when ESC is pressed.
    """

    def __init__(self):
        self._setup_fonts()
        self.buttons = []
        self.selected_index = 0
        self.hover_index = -1
        self._build_buttons()

    def _setup_fonts(self):
        """Initialize fonts."""
        try:
            self.font_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
            self.font_button = pygame.font.SysFont("Segoe UI", 22, bold=True)
            self.font_hint = pygame.font.SysFont("Segoe UI", 14)
        except Exception:
            self.font_title = pygame.font.Font(None, 40)
            self.font_button = pygame.font.Font(None, 26)
            self.font_hint = pygame.font.Font(None, 16)

    def _build_buttons(self):
        """Create button definitions."""
        btn_w = 240
        btn_h = 50
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        self.buttons = [
            {
                "label": "Resume",
                "action": "resume",
                "rect": pygame.Rect(cx - btn_w // 2, cy - 40, btn_w, btn_h),
            },
            {
                "label": "Save & Quit",
                "action": "save_quit",
                "rect": pygame.Rect(cx - btn_w // 2, cy + 25, btn_w, btn_h),
            },
        ]
        self.selected_index = 0

    def show(self, screen, clock, game_state, renderer, input_handler):
        """
        Display the pause overlay and wait for user action.

        Args:
            screen: Pygame display surface
            clock: Pygame clock
            game_state: Current GameState (for background rendering)
            renderer: Renderer instance (for background rendering)
            input_handler: InputHandler instance (for background rendering)

        Returns:
            str: "resume" or "save_quit"
        """
        # Capture the current game frame as background
        bg_snapshot = screen.copy()

        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.hover_index = -1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "save_quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "resume"
                    elif event.key == pygame.K_UP:
                        self.selected_index = (self.selected_index - 1) % len(self.buttons)
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = (self.selected_index + 1) % len(self.buttons)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return self.buttons[self.selected_index]["action"]

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, btn in enumerate(self.buttons):
                        if btn["rect"].collidepoint(mouse_pos):
                            return btn["action"]

            # Update hover
            for i, btn in enumerate(self.buttons):
                if btn["rect"].collidepoint(mouse_pos):
                    self.hover_index = i

            # Draw
            self._draw(screen, bg_snapshot)
            pygame.display.flip()
            clock.tick(60)

    def _draw(self, screen, bg_snapshot):
        """Render the pause overlay."""
        # Draw the frozen game frame
        screen.blit(bg_snapshot, (0, 0))

        # Dark semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        # Panel background
        panel_w = 340
        panel_h = 280
        panel_rect = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2, panel_w, panel_h)
        panel_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surface.fill((30, 28, 26, 230))
        pygame.draw.rect(panel_surface, COLOR_ACCENT, panel_surface.get_rect(), 2, border_radius=12)
        screen.blit(panel_surface, panel_rect.topleft)

        # Title
        title_surf = self.font_title.render("PAUSED", True, COLOR_TEXT_PRIMARY)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, panel_rect.y + 25))

        # Decorative line
        line_y = panel_rect.y + 70
        pygame.draw.line(screen, COLOR_BORDER, (cx - 80, line_y), (cx + 80, line_y), 1)

        # Buttons
        for i, btn in enumerate(self.buttons):
            is_selected = (i == self.selected_index) or (i == self.hover_index)
            self._draw_button(screen, btn, is_selected)

        # Hint
        hint = "ESC Resume  •  ↑↓ Navigate  •  Enter Select"
        hint_surf = self.font_hint.render(hint, True, COLOR_TEXT_SECONDARY)
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, panel_rect.bottom - 35))

    def _draw_button(self, screen, btn, is_selected):
        """Draw a button."""
        rect = btn["rect"]

        if is_selected:
            bg_color = COLOR_ACCENT
            text_color = (255, 255, 255)
            border_color = COLOR_ACCENT
        else:
            bg_color = COLOR_PANEL_BG
            text_color = COLOR_TEXT_PRIMARY
            border_color = COLOR_BORDER

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)

        label_surf = self.font_button.render(btn["label"], True, text_color)
        screen.blit(label_surf, (
            rect.centerx - label_surf.get_width() // 2,
            rect.centery - label_surf.get_height() // 2,
        ))
