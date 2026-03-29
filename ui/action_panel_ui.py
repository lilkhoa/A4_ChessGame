"""
Action Panel UI - Resignation and Draw Offer Buttons

This panel displays Resign and Offer Draw buttons that allow players
to communicate game actions to their opponents.
"""

import pygame
from config import (
    WINDOW_WIDTH, BOARD_WIDTH, SIDEBAR_WIDTH, WINDOW_HEIGHT,
    COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_ACCENT,
    COLOR_TEXT_SECONDARY, SQUARE_SIZE
)


class ActionPanelUI:
    """
    UI panel for communication action buttons (Resign, Offer Draw).
    
    The panel is positioned to the right of the chessboard in the sidebar.
    It tracks button states including the draw offer cooldown to prevent spam.
    """
    
    def __init__(self):
        """Initialize action panel with button layout and state."""
        # Button dimensions and positioning
        self.button_width = 180
        self.button_height = 45
        self.start_x = BOARD_WIDTH + 15
        self.start_y = 50
        self.button_spacing = 15
        
        # Resign button
        self.resign_rect = pygame.Rect(
            self.start_x, self.start_y,
            self.button_width, self.button_height
        )
        
        # Offer Draw button
        self.offer_draw_rect = pygame.Rect(
            self.start_x, self.start_y + self.button_height + self.button_spacing,
            self.button_width, self.button_height
        )
        
        # State tracking
        self.draw_offer_cooldown = 0.0  # Cooldown timer in seconds
        self.draw_offer_cooldown_max = 10.0  # 10 second cooldown before next offer
        
        # Font
        self.font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 10)
    
    def tick(self, delta_time):
        """
        Update button states each frame (decrement cooldown).
        
        Args:
            delta_time: Time elapsed since last frame (in seconds)
        """
        if self.draw_offer_cooldown > 0:
            self.draw_offer_cooldown -= delta_time
    
    def draw(self, screen):
        """
        Draw the action panel with Resign and Offer Draw buttons.
        
        Args:
            screen: Pygame surface to draw on
        """
        # Resign Button (always enabled)
        self._draw_button(
            screen,
            self.resign_rect,
            "Resign",
            enabled=True,
            is_normal=True
        )
        
        # Offer Draw Button (disabled during cooldown)
        is_draw_enabled = self.draw_offer_cooldown <= 0
        self._draw_button(
            screen,
            self.offer_draw_rect,
            "Offer Draw",
            enabled=is_draw_enabled,
            is_normal=True
        )
        
        # Draw cooldown indicator on Offer Draw button if active
        if self.draw_offer_cooldown > 0:
            cooldown_text = f"{self.draw_offer_cooldown:.1f}s"
            cooldown_surface = self.small_font.render(cooldown_text, True, COLOR_TEXT_SECONDARY)
            cx = self.offer_draw_rect.centerx - cooldown_surface.get_width() // 2
            cy = self.offer_draw_rect.centery - cooldown_surface.get_height() // 2
            screen.blit(cooldown_surface, (cx, cy))
    
    def _draw_button(self, screen, rect, text, enabled=True, is_normal=True):
        """
        Draw a single button with text.
        
        Args:
            screen: Pygame surface to draw on
            rect: pygame.Rect defining button position and size
            text: Button label text
            enabled: Whether button is clickable (affects color)
            is_normal: Visual style (True for primary, False for secondary)
        """
        # Button background color (dimmed if disabled)
        if enabled:
            bg_color = COLOR_ACCENT if is_normal else COLOR_PANEL_BG
        else:
            bg_color = (100, 100, 100)  # Dimmed/greyed out
        
        # Draw button background
        pygame.draw.rect(screen, bg_color, rect)
        
        # Draw button border
        border_color = COLOR_BORDER if enabled else (80, 80, 80)
        pygame.draw.rect(screen, border_color, rect, 2)
        
        # Draw text
        text_color = COLOR_TEXT_PRIMARY if enabled else COLOR_TEXT_SECONDARY
        text_surface = self.font.render(text, True, text_color)
        cx = rect.centerx - text_surface.get_width() // 2
        cy = rect.centery - text_surface.get_height() // 2
        screen.blit(text_surface, (cx, cy))
    
    def handle_click(self, mouse_pos):
        """
        Detect which button (if any) was clicked.
        
        Args:
            mouse_pos: Tuple (x, y) of mouse position
        
        Returns:
            str: Button signal ("BTN_RESIGN", "BTN_OFFER_DRAW") or None
        """
        if self.resign_rect.collidepoint(mouse_pos):
            return "BTN_RESIGN"
        
        # Offer Draw only clickable if not in cooldown
        if self.draw_offer_cooldown <= 0 and self.offer_draw_rect.collidepoint(mouse_pos):
            return "BTN_OFFER_DRAW"
        
        return None
    
    def set_draw_offer_cooldown(self, duration=None):
        """
        Activate the draw offer cooldown to prevent spam.
        
        Args:
            duration: Cooldown duration in seconds (default: 10 seconds)
        """
        if duration is None:
            duration = self.draw_offer_cooldown_max
        self.draw_offer_cooldown = duration
    
    def reset(self):
        """Reset all button states."""
        self.draw_offer_cooldown = 0.0