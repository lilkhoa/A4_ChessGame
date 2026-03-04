import pygame
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, SQUARE_SIZE,
    SIDEBAR_WIDTH, COLOR_SIDEBAR_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_DANGER, COLOR_PANEL_BG, COLOR_BORDER, COLOR_BG
)
from ui.board_ui import BoardUI
from ui.piece_ui import PieceUI
from ui.animation import Animation


class Renderer:
    """
    Main renderer that composes all UI elements: board, pieces, highlights,
    sidebar status panel, and game-over overlays.
    """

    def __init__(self):
        self.board_ui = BoardUI()
        self.piece_ui = PieceUI()
        self.animation = Animation()
        self._setup_fonts()
        
        # Load sidebar icon
        import os
        try:
            icon_path = os.path.join("assets", "images", "game-icon.png")
            self.icon_img = pygame.image.load(icon_path).convert_alpha()
            self.icon_img = pygame.transform.smoothscale(self.icon_img, (24, 24))
        except Exception:
            self.icon_img = None

    def _setup_fonts(self):
        """Initialize all fonts used in rendering."""
        try:
            self.font_title = pygame.font.SysFont("Segoe UI", 28, bold=True)
            self.font_heading = pygame.font.SysFont("Segoe UI", 20, bold=True)
            self.font_body = pygame.font.SysFont("Segoe UI", 16)
            self.font_small = pygame.font.SysFont("Segoe UI", 14)
            self.font_large = pygame.font.SysFont("Segoe UI", 42, bold=True)
            self.font_overlay = pygame.font.SysFont("Segoe UI", 22)
        except Exception:
            self.font_title = pygame.font.Font(None, 32)
            self.font_heading = pygame.font.Font(None, 24)
            self.font_body = pygame.font.Font(None, 18)
            self.font_small = pygame.font.Font(None, 16)
            self.font_large = pygame.font.Font(None, 48)
            self.font_overlay = pygame.font.Font(None, 26)

    def draw(self, screen, game_state, input_handler):
        """
        Draw the complete game frame.

        Args:
            screen: Pygame display surface
            game_state: Current GameState object
            input_handler: InputHandler instance for selection/drag state
        """
        # Draw the chessboard
        self.board_ui.draw_board(screen)

        # Draw highlights
        last_move = game_state.move_log[-1] if game_state.move_log else None
        king_check_pos = input_handler.get_king_in_check_pos(game_state)

        self.board_ui.draw_highlights(
            screen,
            selected_sq=input_handler.selected_square,
            valid_moves=input_handler.valid_moves,
            last_move=last_move,
            king_in_check_pos=king_check_pos,
            board_grid=game_state.board
        )

        # Draw pieces (skip dragged piece)
        skip = input_handler.drag_start if input_handler.dragging else None
        self.piece_ui.draw_pieces(screen, game_state.board, skip_pos=skip)

        # Draw dragged piece following mouse
        if input_handler.dragging and input_handler.drag_piece:
            self.piece_ui.draw_piece_at(
                screen, input_handler.drag_piece, input_handler.mouse_pos
            )

        # Draw sidebar
        self.draw_sidebar(screen, game_state)

        # Draw game-over overlay
        if game_state.is_checkmate or game_state.is_draw or game_state.timeout_winner:
            self.draw_game_over_overlay(screen, game_state)

    def draw_sidebar(self, screen, game_state):
        """Draw the status sidebar panel."""
        sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, COLOR_SIDEBAR_BG, sidebar_rect)

        # Decorative top accent line
        pygame.draw.rect(screen, COLOR_ACCENT,
                         pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, 3))

        x_base = BOARD_WIDTH + 12
        panel_w = SIDEBAR_WIDTH - 24
        y = 15

        # Title
        if self.icon_img:
            title_text = self.font_heading.render("Chess Game", True, COLOR_TEXT_PRIMARY)
            icon_y = y + (title_text.get_height() - self.icon_img.get_height()) // 2
            screen.blit(self.icon_img, (x_base, icon_y))
            screen.blit(title_text, (x_base + self.icon_img.get_width() + 8, y))
        else:
            title = self.font_heading.render("♚ Chess Game", True, COLOR_TEXT_PRIMARY)
            screen.blit(title, (x_base, y))
        y += 32

        # Divider
        pygame.draw.line(screen, COLOR_BORDER,
                         (x_base, y), (x_base + panel_w, y))
        y += 10

        # Current turn panel
        y = self._draw_turn_panel(screen, game_state, x_base, y, panel_w)
        y += 8

        # Timers
        y = self._draw_timers(screen, game_state, x_base, y, panel_w)
        y += 8

        # Move history info
        y = self._draw_move_info(screen, game_state, x_base, y, panel_w)
        y += 8

        # Game status
        y = self._draw_status_info(screen, game_state, x_base, y, panel_w)
        y += 12

        # Controls help
        self._draw_controls_help(screen, x_base, WINDOW_HEIGHT - 100)

    def _draw_turn_panel(self, screen, game_state, x, y, panel_w):
        """Draw the current turn indicator panel."""
        panel_h = 52
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect, border_radius=6)

        label = self.font_small.render("TURN", True, COLOR_TEXT_SECONDARY)
        screen.blit(label, (x + 10, y + 6))

        turn = game_state.current_turn
        circle_color = (255, 255, 255) if turn == "white" else (50, 50, 50)
        circle_border = (180, 180, 180) if turn == "white" else (100, 100, 100)
        pygame.draw.circle(screen, circle_color, (x + 20, y + 34), 8)
        pygame.draw.circle(screen, circle_border, (x + 20, y + 34), 8, 2)

        turn_text = self.font_body.render(turn.capitalize(), True, COLOR_TEXT_PRIMARY)
        screen.blit(turn_text, (x + 34, y + 26))

        return y + panel_h

    def _draw_timers(self, screen, game_state, x, y, panel_w):
        """Draw player clocks."""
        panel_h = 96
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect, border_radius=6)

        label = self.font_small.render("CLOCKS", True, COLOR_TEXT_SECONDARY)
        screen.blit(label, (x + 10, y + 8))

        def format_time(seconds):
            m = int(max(0, seconds) // 60)
            s = int(max(0, seconds) % 60)
            return f"{m:02d}:{s:02d}"

        # White time
        w_active = game_state.current_turn == "white"
        w_bg = (60, 60, 60) if w_active else (35, 33, 30)
        w_rect = pygame.Rect(x + 10, y + 30, panel_w - 20, 26)
        pygame.draw.rect(screen, w_bg, w_rect, border_radius=4)
        
        w_time_str = format_time(game_state.white_time)
        if game_state.white_time <= 10.0 and game_state.white_time > 0:
            w_color = COLOR_DANGER
        else:
            w_color = COLOR_TEXT_PRIMARY if w_active else COLOR_TEXT_SECONDARY
        w_text = self.font_body.render(f"W: {w_time_str}", True, w_color)
        screen.blit(w_text, (x + 18, y + 33))

        # Black time
        b_active = game_state.current_turn == "black"
        b_bg = (60, 60, 60) if b_active else (35, 33, 30)
        b_rect = pygame.Rect(x + 10, y + 62, panel_w - 20, 26)
        pygame.draw.rect(screen, b_bg, b_rect, border_radius=4)

        b_time_str = format_time(game_state.black_time)
        if game_state.black_time <= 10.0 and game_state.black_time > 0:
            b_color = COLOR_DANGER
        else:
            b_color = COLOR_TEXT_PRIMARY if b_active else COLOR_TEXT_SECONDARY
        b_text = self.font_body.render(f"B: {b_time_str}", True, b_color)
        screen.blit(b_text, (x + 18, y + 65))

        return y + panel_h

    def _draw_move_info(self, screen, game_state, x, y, panel_w):
        """Draw move count information."""
        panel_h = 48
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect, border_radius=6)

        label = self.font_small.render("MOVES", True, COLOR_TEXT_SECONDARY)
        screen.blit(label, (x + 10, y + 6))

        move_count = len(game_state.move_log)
        count_text = self.font_body.render(str(move_count), True, COLOR_ACCENT)
        screen.blit(count_text, (x + 10, y + 24))

        turn_num = (move_count // 2) + 1
        turn_label = self.font_small.render(f"Turn {turn_num}", True, COLOR_TEXT_SECONDARY)
        screen.blit(turn_label, (x + 60, y + 26))

        return y + panel_h

    def _draw_status_info(self, screen, game_state, x, y, panel_w):
        """Draw game status (check, checkmate, stalemate)."""
        panel_h = 48
        panel_rect = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect, border_radius=6)

        label = self.font_small.render("STATUS", True, COLOR_TEXT_SECONDARY)
        screen.blit(label, (x + 10, y + 6))

        if game_state.timeout_winner:
            status = f"Timeout! {game_state.timeout_winner.capitalize()} wins"
            color = COLOR_DANGER
        elif game_state.is_checkmate:
            winner = "Black" if game_state.current_turn == "white" else "White"
            status = f"Checkmate! {winner} wins"
            color = COLOR_DANGER
        elif game_state.is_draw:
            # Show specific draw reason
            if game_state.draw_reason == 'stalemate':
                status = "Draw (Stalemate)"
            elif game_state.draw_reason == 'threefold_repetition':
                status = "Draw (3-fold rep.)"
            elif game_state.draw_reason == 'insufficient_material':
                status = "Draw (Insuff. mat.)"
            elif game_state.draw_reason == 'fifty_move_rule':
                status = "Draw (50-move rule)"
            else:
                status = "Draw"
            color = (255, 193, 37)
        else:
            status = "In progress"
            color = COLOR_ACCENT

        status_text = self.font_small.render(status, True, color)
        screen.blit(status_text, (x + 10, y + 26))

        return y + panel_h

    def _draw_controls_help(self, screen, x, y):
        """Draw keyboard shortcut help at the bottom of the sidebar."""
        controls = [
            ("ESC", "Pause / Menu"),
        ]
        
        label = self.font_small.render("CONTROLS", True, COLOR_TEXT_SECONDARY)
        screen.blit(label, (x, y))
        y += 20

        for key, desc in controls:
            key_surface = self.font_small.render(f"[{key}]", True, COLOR_ACCENT)
            desc_surface = self.font_small.render(f"  {desc}", True, COLOR_TEXT_SECONDARY)
            screen.blit(key_surface, (x, y))
            screen.blit(desc_surface, (x + key_surface.get_width(), y))
            y += 22

    def draw_game_over_overlay(self, screen, game_state):
        """Draw a semi-transparent overlay with game over results."""
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        if game_state.timeout_winner:
            title = "TIME OUT"
            subtitle = f"{game_state.timeout_winner.capitalize()} wins on time"
        elif game_state.is_checkmate:
            winner = "Black" if game_state.current_turn == "white" else "White"
            title = "CHECKMATE"
            subtitle = f"{winner} wins!"
        elif game_state.is_draw:
            title = "DRAW"
            # Show specific draw reason if available
            if game_state.draw_reason == 'stalemate':
                subtitle = "Stalemate"
            elif game_state.draw_reason == 'threefold_repetition':
                subtitle = "Threefold repetition"
            elif game_state.draw_reason == 'insufficient_material':
                subtitle = "Insufficient material"
            elif game_state.draw_reason == 'fifty_move_rule':
                subtitle = "Fifty-move rule"
            else:
                subtitle = "Game drawn"
        else:
            title = "GAME OVER"
            subtitle = "Game ended"

        # Render text centered on the board
        text1 = self.font_large.render(title, True, (255, 255, 255))
        text2 = self.font_overlay.render(subtitle, True, (200, 200, 200))
        restart_text = self.font_body.render("Press ESC for Menu", True, COLOR_ACCENT)

        cx = BOARD_WIDTH // 2

        # Background panel for text
        panel_w = max(text1.get_width(), text2.get_width(), restart_text.get_width()) + 60
        panel_h = 140
        panel_rect = pygame.Rect(
            cx - panel_w // 2,
            BOARD_HEIGHT // 2 - panel_h // 2,
            panel_w, panel_h
        )
        panel_bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_bg.fill((30, 30, 30, 220))
        pygame.draw.rect(panel_bg, COLOR_ACCENT, panel_bg.get_rect(), 2, border_radius=12)
        screen.blit(panel_bg, panel_rect.topleft)

        screen.blit(text1, (cx - text1.get_width() // 2, panel_rect.y + 15))
        screen.blit(text2, (cx - text2.get_width() // 2, panel_rect.y + 65))
        screen.blit(restart_text, (cx - restart_text.get_width() // 2, panel_rect.y + 100))
