"""
Dialog UI - Draw Offer Response Dialog

Displays a modal dialog when opponent offers a draw, requiring player to
accept or decline the offer before game can continue.
"""

import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_PANEL_BG, COLOR_TEXT_PRIMARY, COLOR_BORDER, COLOR_ACCENT,
    COLOR_DANGER
)


class DrawOfferDialog:
    """
    Modal dialog displayed when opponent offers a draw.
    
    This dialog blocks game interaction until player responds (Accept/Decline).
    """
    
    def __init__(self):
        """Initialize draw offer dialog."""
        # Dialog dimensions and position (centered on screen)
        self.dialog_width = 400
        self.dialog_height = 200
        self.dialog_x = (WINDOW_WIDTH - self.dialog_width) // 2
        self.dialog_y = (WINDOW_HEIGHT - self.dialog_height) // 2
        self.dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        
        # Button dimensions
        self.button_width = 120
        self.button_height = 40
        self.button_spacing = 20
        
        # Accept button (left side, green)
        self.accept_rect = pygame.Rect(
            self.dialog_x + 40,
            self.dialog_y + self.dialog_height - 60,
            self.button_width,
            self.button_height
        )
        
        # Decline button (right side, red)
        self.decline_rect = pygame.Rect(
            self.dialog_x + self.dialog_width - self.button_width - 40,
            self.dialog_y + self.dialog_height - 60,
            self.button_width,
            self.button_height
        )
        
        # State
        self.visible = False
        self.hover_button = None  # "accept", "decline", or None
        
        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.button_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
    
    def open(self):
        """Display the draw offer dialog."""
        self.visible = True
        self.hover_button = None
    
    def close(self):
        """Hide the draw offer dialog."""
        self.visible = False
        self.hover_button = None
    
    def draw(self, screen):
        """
        Draw the dialog with title text and buttons.
        
        Args:
            screen: Pygame surface to draw on
        """
        if not self.visible:
            return
        
        # Semi-transparent overlay behind dialog
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Dialog background
        pygame.draw.rect(screen, COLOR_PANEL_BG, self.dialog_rect)
        pygame.draw.rect(screen, COLOR_BORDER, self.dialog_rect, 3)
        
        # Title text
        title_surface = self.title_font.render("Opponent offers a draw", True, COLOR_TEXT_PRIMARY)
        title_x = self.dialog_rect.centerx - title_surface.get_width() // 2
        title_y = self.dialog_y + 30
        screen.blit(title_surface, (title_x, title_y))
        
        # Accept button
        self._draw_button(
            screen,
            self.accept_rect,
            "Accept",
            COLOR_ACCENT,
            self.hover_button == "accept"
        )
        
        # Decline button
        self._draw_button(
            screen,
            self.decline_rect,
            "Decline",
            COLOR_DANGER,
            self.hover_button == "decline"
        )
    
    def _draw_button(self, screen, rect, text, base_color, is_hover=False):
        """
        Draw a single dialog button.
        
        Args:
            screen: Pygame surface to draw on
            rect: pygame.Rect defining button position
            text: Button label
            base_color: Base button color
            is_hover: Whether button is being hovered over
        """
        # Brighten color on hover
        if is_hover:
            color = tuple(min(c + 40, 255) for c in base_color)
        else:
            color = base_color
        
        # Draw button background
        pygame.draw.rect(screen, color, rect)
        
        # Draw button border
        pygame.draw.rect(screen, COLOR_BORDER, rect, 2)
        
        # Draw text
        text_surface = self.button_font.render(text, True, COLOR_TEXT_PRIMARY)
        cx = rect.centerx - text_surface.get_width() // 2
        cy = rect.centery - text_surface.get_height() // 2
        screen.blit(text_surface, (cx, cy))
    
    def handle_click(self, mouse_pos):
        """
        Detect which button (if any) was clicked.
        
        Args:
            mouse_pos: Tuple (x, y) of mouse position
        
        Returns:
            str: Button signal ("ACCEPT_DRAW", "DECLINE_DRAW") or None
        """
        if not self.visible:
            return None
        
        if self.accept_rect.collidepoint(mouse_pos):
            return "ACCEPT_DRAW"
        
        if self.decline_rect.collidepoint(mouse_pos):
            return "DECLINE_DRAW"
        
        return None
    
    def handle_mousemotion(self, mouse_pos):
        """
        Update hover state based on mouse position.
        
        Args:
            mouse_pos: Tuple (x, y) of mouse position
        """
        if not self.visible:
            self.hover_button = None
            return
        
        if self.accept_rect.collidepoint(mouse_pos):
            self.hover_button = "accept"
        elif self.decline_rect.collidepoint(mouse_pos):
            self.hover_button = "decline"
        else:
            self.hover_button = None
    
    def is_visible(self):
        """Check if dialog is currently visible."""
        return self.visible