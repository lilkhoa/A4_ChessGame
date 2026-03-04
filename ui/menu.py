# ui/menu.py

import pygame
import sys
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG, COLOR_SIDEBAR_BG,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT,
    COLOR_PANEL_BG, COLOR_BORDER
)


class MainMenu:
    """
    Main menu screen with New Game / Continue / Quit options.
    Rendered on the full game window before gameplay starts.
    """

    def __init__(self):
        self._setup_fonts()
        self.buttons = []
        self.selected_index = 0
        self.hover_index = -1
        self.state = "main"

    def _setup_fonts(self):
        """Initialize fonts for the menu."""
        try:
            self.font_title = pygame.font.SysFont("Segoe UI", 56, bold=True)
            self.font_subtitle = pygame.font.SysFont("Segoe UI", 18)
            self.font_button = pygame.font.SysFont("Segoe UI", 24, bold=True)
            self.font_hint = pygame.font.SysFont("Segoe UI", 14)
        except Exception:
            self.font_title = pygame.font.Font(None, 64)
            self.font_subtitle = pygame.font.Font(None, 22)
            self.font_button = pygame.font.Font(None, 28)
            self.font_hint = pygame.font.Font(None, 16)

    def show(self, screen, clock, has_save=False):
        """
        Display the main menu and wait for user input.

        Args:
            screen: Pygame display surface
            clock: Pygame clock for frame rate control
            has_save: Whether a save file exists (enables Continue)

        Returns:
            dict: Payload containing selected action, mode, and difficulty
        """
        self.state = "main"
        self._build_buttons(has_save)

        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.hover_index = -1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {"action": "quit"}

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "main":
                            return {"action": "quit"}
                        else:
                            self._handle_action("back", has_save)
                    elif event.key == pygame.K_UP:
                        self._move_selection(-1)
                    elif event.key == pygame.K_DOWN:
                        self._move_selection(1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        action = self.buttons[self.selected_index]["action"]
                        if self.buttons[self.selected_index]["enabled"]:
                            payload = self._handle_action(action, has_save)
                            if payload:
                                return payload

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, btn in enumerate(self.buttons):
                        if btn["enabled"] and btn["rect"].collidepoint(mouse_pos):
                            payload = self._handle_action(btn["action"], has_save)
                            if payload:
                                return payload

            # Update hover state
            for i, btn in enumerate(self.buttons):
                if btn["enabled"] and btn["rect"].collidepoint(mouse_pos):
                    self.hover_index = i

            self._draw(screen, has_save)
            pygame.display.flip()
            clock.tick(60)

    def _handle_action(self, action, has_save):
        """Handle an action from a button press, updating state or returning payload."""
        if self.state == "main":
            if action == "new_game":
                self.state = "mode_select"
                self._build_buttons(has_save)
                return None
            else:
                return {"action": action}
        elif self.state == "mode_select":
            if action == "back":
                self.state = "main"
                self._build_buttons(has_save)
                return None
            elif action == "1p":
                self.state = "difficulty_select"
                self._build_buttons(has_save)
                return None
            elif action == "2p":
                return {"action": "new_game", "mode": "2p", "difficulty": None}
        elif self.state == "difficulty_select":
            if action == "back":
                self.state = "mode_select"
                self._build_buttons(has_save)
                return None
            else:
                return {"action": "new_game", "mode": "1p", "difficulty": action}
        return None

    def _build_buttons(self, has_save):
        """Create button definitions with positions."""
        btn_w = 280
        btn_h = 54
        cx = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 - 10

        if self.state == "main":
            self.buttons = [
                {
                    "label": "Continue",
                    "action": "continue",
                    "enabled": has_save,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h),
                },
                {
                    "label": "New Game",
                    "action": "new_game",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 72, btn_w, btn_h),
                },
                {
                    "label": "Quit",
                    "action": "quit",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 144, btn_w, btn_h),
                },
            ]
            self.selected_index = 0 if has_save else 1
            
        elif self.state == "mode_select":
            self.buttons = [
                {
                    "label": "1 Player (vs AI)",
                    "action": "1p",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h),
                },
                {
                    "label": "2 Players",
                    "action": "2p",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 72, btn_w, btn_h),
                },
                {
                    "label": "Back",
                    "action": "back",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 144, btn_w, btn_h),
                },
            ]
            self.selected_index = 0
            
        elif self.state == "difficulty_select":
            self.buttons = [
                {
                    "label": "Easy",
                    "action": "easy",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y - 36, btn_w, btn_h),
                },
                {
                    "label": "Medium",
                    "action": "medium",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 36, btn_w, btn_h),
                },
                {
                    "label": "Hard",
                    "action": "hard",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 108, btn_w, btn_h),
                },
                {
                    "label": "Back",
                    "action": "back",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 180, btn_w, btn_h),
                },
            ]
            self.selected_index = 0

    def _move_selection(self, direction):
        """Move keyboard selection up or down, skipping disabled buttons."""
        n = len(self.buttons)
        idx = self.selected_index
        for _ in range(n):
            idx = (idx + direction) % n
            if self.buttons[idx]["enabled"]:
                self.selected_index = idx
                return

    def _draw(self, screen, has_save):
        """Render the full menu screen."""
        # Background
        screen.fill(COLOR_BG)

        cx = WINDOW_WIDTH // 2

        # -- Decorative top accent bar --
        pygame.draw.rect(screen, COLOR_ACCENT, pygame.Rect(0, 0, WINDOW_WIDTH, 4))

        # -- Title --
        title_surf = self.font_title.render("♚ Chess", True, COLOR_TEXT_PRIMARY)
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, 100))

        # -- Subtitle --
        subtitle_text = "A classic chess experience"
        if self.state == "mode_select":
            subtitle_text = "Select Game Mode"
        elif self.state == "difficulty_select":
            subtitle_text = "Select AI Difficulty"

        subtitle_surf = self.font_subtitle.render(
            subtitle_text, True, COLOR_TEXT_SECONDARY
        )
        screen.blit(subtitle_surf, (cx - subtitle_surf.get_width() // 2, 170))

        # -- Decorative line --
        line_w = 200
        pygame.draw.line(
            screen, COLOR_BORDER,
            (cx - line_w // 2, 210), (cx + line_w // 2, 210), 2
        )

        # -- Buttons --
        for i, btn in enumerate(self.buttons):
            is_selected = (i == self.selected_index) or (i == self.hover_index)
            self._draw_button(screen, btn, is_selected)

        # -- Hint text at bottom --
        hint = "↑↓ Navigate  •  Enter Select  •  ESC Quit"
        hint_surf = self.font_hint.render(hint, True, COLOR_TEXT_SECONDARY)
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, WINDOW_HEIGHT - 40))

    def _draw_button(self, screen, btn, is_selected):
        """Draw a single menu button."""
        rect = btn["rect"]
        enabled = btn["enabled"]

        if not enabled:
            # Disabled style
            bg_color = (50, 48, 45)
            text_color = (100, 100, 100)
            border_color = (60, 58, 55)
        elif is_selected:
            # Highlighted style
            bg_color = COLOR_ACCENT
            text_color = (255, 255, 255)
            border_color = COLOR_ACCENT
        else:
            # Normal style
            bg_color = COLOR_PANEL_BG
            text_color = COLOR_TEXT_PRIMARY
            border_color = COLOR_BORDER

        # Button background with rounded corners
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)

        # Button label
        label_surf = self.font_button.render(btn["label"], True, text_color)
        lx = rect.centerx - label_surf.get_width() // 2
        ly = rect.centery - label_surf.get_height() // 2
        screen.blit(label_surf, (lx, ly))

        # Disabled hint text
        if not enabled and btn["action"] == "continue":
            hint_surf = self.font_hint.render("No saved game", True, (80, 80, 80))
            screen.blit(hint_surf, (rect.centerx - hint_surf.get_width() // 2, rect.bottom + 4))
