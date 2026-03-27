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

    def __init__(self, timer_ui=None):
        self.board_ui = BoardUI()
        self.piece_ui = PieceUI()
        self.animation = Animation()
        self.timer_ui = timer_ui
        self._setup_fonts()
        
        # Load avatars
        import os
        self.avatar_player = None
        self.avatar_computer = None
        try:
            player_path = os.path.join("assets", "images", "avatar", "player.jpg")
            computer_path = os.path.join("assets", "images", "avatar", "computer.jpg")
            self.avatar_player = pygame.image.load(player_path).convert()
            self.avatar_computer = pygame.image.load(computer_path).convert()
        except Exception as e:
            print(f"Warning: Could not load avatars: {e}")

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

    def draw(self, screen, game_state, input_handler, game_controller=None):
        """
        Draw the complete game frame.

        Args:
            screen: Pygame display surface
            game_state: Current GameState object
            input_handler: InputHandler instance for selection/drag state
            game_controller: GameController instance for AI info (optional)
        """
        # Determine if board should be reversed (player is black vs AI)
        reversed_view = False
        if game_controller and hasattr(game_controller, 'ai_agent') and game_controller.ai_agent:
            # If AI is white, then human is black, so reverse the board
            if game_controller.ai_color == 'white':
                reversed_view = True
        
        # Draw the chessboard
        self.board_ui.draw_board(screen, reversed_view)

        # Draw highlights
        last_move = game_state.move_log[-1] if game_state.move_log else None
        king_check_pos = input_handler.get_king_in_check_pos(game_state)

        self.board_ui.draw_highlights(
            screen,
            selected_sq=input_handler.selected_square,
            valid_moves=input_handler.valid_moves,
            last_move=last_move,
            king_in_check_pos=king_check_pos,
            board_grid=game_state.board,
            reversed_view=reversed_view
        )

        # Draw pieces (skip dragged piece)
        skip = input_handler.drag_start if input_handler.dragging else None
        self.piece_ui.draw_pieces(screen, game_state.board, skip_pos=skip, reversed_view=reversed_view)

        # Draw dragged piece following mouse
        if input_handler.dragging and input_handler.drag_piece:
            self.piece_ui.draw_piece_at(
                screen, input_handler.drag_piece, input_handler.mouse_pos
            )

        # Draw new player panels sidebar
        self.draw_player_panels(screen, game_state, game_controller)

        # Draw game-over overlay
        if game_state.is_checkmate or game_state.is_draw or game_state.timeout_winner:
            self.draw_game_over_overlay(screen, game_state)

    def draw_player_panels(self, screen, game_state, game_controller):
        """Draw the new player panel design in the sidebar."""
        sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, COLOR_SIDEBAR_BG, sidebar_rect)
        
        # Determine player info
        ai_color = None
        ai_name = None
        is_human_vs_human = True
        reversed_view = False
        
        if game_controller and hasattr(game_controller, 'ai_agent') and game_controller.ai_agent:
            ai_color = game_controller.ai_color
            ai_name = game_controller.ai_agent.name
            is_human_vs_human = False
            # If AI is white, human is black, so reverse the board view
            if ai_color == 'white':
                reversed_view = True
        
        # Get captured pieces
        white_captured, black_captured = self._get_captured_pieces(game_state)
        
        # Calculate material advantage
        white_material = self._calculate_material_value(white_captured)
        black_material = self._calculate_material_value(black_captured)
        
        # Calculate panel positions
        panel_height = 140
        spacing = 20
        top_panel_y = spacing
        bottom_panel_y = WINDOW_HEIGHT - panel_height - spacing
        
        # When reversed (playing as black), show black panel at bottom
        if reversed_view:
            # Black panel at bottom (player's side)
            black_avatar = self.avatar_player  # Human is black
            black_name = "Player"
            black_active = game_state.current_turn == 'black'
            self._draw_player_panel(
                screen,
                x=BOARD_WIDTH,
                y=bottom_panel_y,
                width=SIDEBAR_WIDTH,
                height=panel_height,
                avatar=black_avatar,
                player_name=black_name,
                color='black',
                time_remaining=game_state.black_time,
                captured_pieces=black_captured,  # Black captured white pieces
                material_advantage=black_material - white_material,
                is_active=black_active
            )
            
            # White panel at top (AI's side)
            white_avatar = self.avatar_computer  # AI is white
            white_name = ai_name
            white_active = game_state.current_turn == 'white'
            self._draw_player_panel(
                screen,
                x=BOARD_WIDTH,
                y=top_panel_y,
                width=SIDEBAR_WIDTH,
                height=panel_height,
                avatar=white_avatar,
                player_name=white_name,
                color='white',
                time_remaining=game_state.white_time,
                captured_pieces=white_captured,  # White captured black pieces
                material_advantage=white_material - black_material,
                is_active=white_active
            )
        else:
            # Normal view: White at bottom
            white_avatar = self.avatar_computer if ai_color == 'white' else self.avatar_player
            white_name = ai_name if ai_color == 'white' else ("Player 1" if is_human_vs_human else "Player")
            white_active = game_state.current_turn == 'white'
            self._draw_player_panel(
                screen,
                x=BOARD_WIDTH,
                y=bottom_panel_y,
                width=SIDEBAR_WIDTH,
                height=panel_height,
                avatar=white_avatar,
                player_name=white_name,
                color='white',
                time_remaining=game_state.white_time,
                captured_pieces=white_captured,  # White captured black pieces
                material_advantage=white_material - black_material,
                is_active=white_active
            )
            
            # Black panel at top
            black_avatar = self.avatar_computer if ai_color == 'black' else self.avatar_player
            black_name = ai_name if ai_color == 'black' else ("Player 2" if is_human_vs_human else "Player")
            black_active = game_state.current_turn == 'black'
            self._draw_player_panel(
                screen,
                x=BOARD_WIDTH,
                y=top_panel_y,
                width=SIDEBAR_WIDTH,
                height=panel_height,
                avatar=black_avatar,
                player_name=black_name,
                color='black',
                time_remaining=game_state.black_time,
                captured_pieces=black_captured,  # Black captured white pieces
                material_advantage=black_material - white_material,
                is_active=black_active
            )
    
    def _draw_player_panel(self, screen, x, y, width, height, avatar, player_name, 
                          color, time_remaining, captured_pieces, material_advantage, is_active):
        """Draw a single player panel."""
        # Panel background
        panel_rect = pygame.Rect(x + 10, y, width - 20, height)
        
        # Active player highlight/glow
        if is_active:
            # Glowing border
            glow_color = (129, 182, 76, 200)  # COLOR_ACCENT with alpha
            glow_surface = pygame.Surface((panel_rect.width + 6, panel_rect.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=8, width=3)
            screen.blit(glow_surface, (panel_rect.x - 3, panel_rect.y - 3))
            bg_color = (65, 63, 60)
        else:
            bg_color = COLOR_PANEL_BG
        
        pygame.draw.rect(screen, bg_color, panel_rect, border_radius=6)
        
        # Avatar (top left)
        avatar_size = 50
        avatar_x = panel_rect.x + 10
        avatar_y = panel_rect.y + 10
        if avatar:
            avatar_scaled = pygame.transform.smoothscale(avatar, (avatar_size, avatar_size))
            screen.blit(avatar_scaled, (avatar_x, avatar_y))
        else:
            # Fallback: draw colored circle
            circle_color = (255, 255, 255) if color == 'white' else (50, 50, 50)
            pygame.draw.circle(screen, circle_color, (avatar_x + avatar_size//2, avatar_y + avatar_size//2), avatar_size//2)
        
        # Player name (next to avatar)
        name_x = avatar_x + avatar_size + 10
        name_y = avatar_y + 5
        name_text = self.font_body.render(player_name, True, COLOR_TEXT_PRIMARY)
        screen.blit(name_text, (name_x, name_y))
        
        # Timer (right side, same row as name)
        if self.timer_ui:
            # Use TimerUI for rendering (cleaner separation of concerns)
            timer_x = panel_rect.x + panel_rect.width - 65
            timer_y = avatar_y
            self.timer_ui.render_time(screen, timer_x, timer_y, time_remaining, is_active=False)
        else:
            # Fallback: inline rendering
            timer_text = self._format_time(time_remaining)
            if time_remaining <= 10.0 and time_remaining > 0:
                timer_color = COLOR_DANGER
            else:
                timer_color = COLOR_TEXT_PRIMARY
            time_surface = self.font_heading.render(timer_text, True, timer_color)
            time_x = panel_rect.x + panel_rect.width - time_surface.get_width() - 10
            time_y = avatar_y
            
            # Timer background
            timer_bg_rect = pygame.Rect(time_x - 5, time_y - 2, time_surface.get_width() + 10, time_surface.get_height() + 4)
            pygame.draw.rect(screen, (40, 38, 35), timer_bg_rect, border_radius=4)
            screen.blit(time_surface, (time_x, time_y))
        
        # Captured pieces display (below avatar)
        captured_y = avatar_y + avatar_size + 15
        self._draw_captured_pieces(screen, panel_rect.x + 10, captured_y, captured_pieces, material_advantage, panel_rect.width - 20)
    
    def _draw_captured_pieces(self, screen, x, y, captured_pieces, material_advantage, max_width):
        """Draw captured pieces with material advantage."""
        piece_size = 16  # Reduced for more compact display
        spacing = 1       # Minimal gap between pieces
        current_x = x
        
        # Order: Queen, Rook, Bishop, Knight, Pawn
        piece_order = ['queen', 'rook', 'bishop', 'knight', 'pawn']
        
        for piece_name in piece_order:
            count = captured_pieces.get(piece_name, 0)
            for _ in range(count):
                if current_x + piece_size > x + max_width - 25:  # Leave space for advantage
                    break
                
                # Draw small piece icon
                piece_sprite = self.piece_ui.get_small_piece_sprite(piece_name, captured_pieces.get('_color', 'white'))
                if piece_sprite:
                    piece_scaled = pygame.transform.smoothscale(piece_sprite, (piece_size, piece_size))
                    screen.blit(piece_scaled, (current_x, y))
                else:
                    # Fallback: draw colored square
                    pygame.draw.rect(screen, (100, 100, 100), (current_x, y, piece_size, piece_size))
                
                current_x += piece_size + spacing
        
        # Material advantage (only if positive)
        if material_advantage > 0:
            advantage_text = f"+{material_advantage}"
            advantage_surface = self.font_small.render(advantage_text, True, COLOR_ACCENT)  # Use smaller font
            advantage_x = x + max_width - advantage_surface.get_width()
            screen.blit(advantage_surface, (advantage_x, y))
    
    def _get_captured_pieces(self, game_state):
        """
        Parse move log to get captured pieces for each player.
        Returns: (white_captured, black_captured) - dicts with piece counts and color
        """
        white_captured = {'_color': 'black', 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0}
        black_captured = {'_color': 'white', 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0}
        
        for move_entry in game_state.move_log:
            captured = move_entry.get('captured')
            if captured:
                piece_name = captured.name
                piece_color = captured.color
                
                if piece_color == 'black':
                    # White captured a black piece
                    white_captured[piece_name] = white_captured.get(piece_name, 0) + 1
                else:
                    # Black captured a white piece
                    black_captured[piece_name] = black_captured.get(piece_name, 0) + 1
        
        return white_captured, black_captured
    
    def _calculate_material_value(self, captured_pieces):
        """Calculate total material value of captured pieces."""
        values = {'queen': 9, 'rook': 5, 'bishop': 3, 'knight': 3, 'pawn': 1}
        total = 0
        for piece_name, count in captured_pieces.items():
            if piece_name != '_color':
                total += values.get(piece_name, 0) * count
        return total
    
    def _format_time(self, seconds):
        """Format time as MM:SS."""
        m = int(max(0, seconds) // 60)
        s = int(max(0, seconds) % 60)
        return f"{m:02d}:{s:02d}"

    def draw_sidebar(self, screen, game_state):
        """Deprecated - kept for compatibility. Use draw_player_panels instead."""
        pass

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
            title = self.font_heading.render("Chess Game", True, COLOR_TEXT_PRIMARY)
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
