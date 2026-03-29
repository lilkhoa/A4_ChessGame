import pygame
from config import COLOR_TEXT_PRIMARY, COLOR_DANGER


class TimerUI:
    """Timer UI renderer."""
    
    def __init__(self, timer, font):
        self.timer = timer
        self.font = font
        self.blink_interval = 0.5
        self.blink_time = 0.0
        self.is_blinking = False
    
    def tick(self, delta_time):
        """Update the blink state for low-time warning."""
        self.blink_time += delta_time
        if self.blink_time >= self.blink_interval:
            self.blink_time = 0.0
            self.is_blinking = not self.is_blinking
    
    def format_time(self, seconds):
        """Format time as MM:SS or MM:SS.ms for display."""
        seconds = max(0, seconds)
        if seconds < 10.0:
            minutes = int(seconds) // 60
            secs = int(seconds) % 60
            ms = int((seconds * 100) % 100)
            return f"{minutes:02d}:{secs:02d}.{ms:02d}"
        else:
            minutes = int(seconds) // 60
            secs = int(seconds) % 60
            return f"{minutes:02d}:{secs:02d}"
    
    def get_time_color(self, time_remaining):
        """Get the color for timer text based on time remaining."""
        if time_remaining <= 0:
            return COLOR_DANGER
        if time_remaining <= 10.0:
            if self.is_blinking:
                return COLOR_DANGER
            else:
                return (100, 100, 100)
        return COLOR_TEXT_PRIMARY
    
    def render_time(self, screen, x, y, time_remaining, is_active=False):
        """Render a timer display at the given position."""
        timer_text = self.format_time(time_remaining)
        timer_color = self.get_time_color(time_remaining)
        text_surface = self.font.render(timer_text, True, timer_color)
        bg_rect = pygame.Rect(x - 5, y - 2, text_surface.get_width() + 10, text_surface.get_height() + 4)
        pygame.draw.rect(screen, (40, 38, 35), bg_rect, border_radius=4)
        if is_active:
            pygame.draw.rect(screen, timer_color, bg_rect, border_radius=4, width=2)
        screen.blit(text_surface, (x, y))
    
    def draw_white_timer(self, screen, x, y):
        """Draw white's timer at the specified position."""
        is_active = self.timer.current_turn == 'white' and self.timer.is_running
        self.render_time(screen, x, y, self.timer.white_time, is_active)
    
    def draw_black_timer(self, screen, x, y):
        """Draw black's timer at the specified position."""
        is_active = self.timer.current_turn == 'black' and self.timer.is_running
        self.render_time(screen, x, y, self.timer.black_time, is_active)
