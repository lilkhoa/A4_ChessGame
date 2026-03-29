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
    Main menu screen with New Game / Continue / Quit options,
    plus Online Multiplayer flows.
    """

    def __init__(self):
        self._setup_fonts()
        import os
        try:
            icon_path = os.path.join("assets", "images", "game-icon.png")
            self.icon_img = pygame.image.load(icon_path).convert_alpha()
            self.icon_img = pygame.transform.smoothscale(self.icon_img, (48, 48))
        except Exception:
            self.icon_img = None
            
        self.buttons = []
        self.selected_index = 0
        self.hover_index = -1
        self.state = "main"
        self._temp_difficulty = None
        
        # Text input state
        self.text_inputs = {}
        self.active_input = None
        self.backspace_timer = 0
        
        # Online state
        self.network_client = None
        self.error_message = ""
        self.error_timer = 0

    def _setup_fonts(self):
        try:
            self.font_title = pygame.font.SysFont("Segoe UI", 56, bold=True)
            self.font_subtitle = pygame.font.SysFont("Segoe UI", 18)
            self.font_button = pygame.font.SysFont("Segoe UI", 24, bold=True)
            self.font_hint = pygame.font.SysFont("Segoe UI", 14)
            self.font_input = pygame.font.SysFont("Segoe UI", 22)
            self.font_error = pygame.font.SysFont("Segoe UI", 16)
        except Exception:
            pygame.font.init()
            self.font_title = pygame.font.Font(None, 64)
            self.font_subtitle = pygame.font.Font(None, 22)
            self.font_button = pygame.font.Font(None, 28)
            self.font_hint = pygame.font.Font(None, 16)
            self.font_input = pygame.font.Font(None, 26)
            self.font_error = pygame.font.Font(None, 20)

    def show(self, screen, clock, has_save=False, network_client=None):
        self.state = "main"
        self.network_client = network_client
        self.error_message = ""
        
        # Initialize inputs
        self.text_inputs = {
            "ip": "127.0.0.1",
            "room_id": ""
        }
        self.active_input = None
        
        self._build_buttons(has_save)

        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.hover_index = -1
            
            # Reset error message after 3 seconds
            if self.error_message and pygame.time.get_ticks() - self.error_timer > 3000:
                self.error_message = ""

            # Poll network client during lobby or room select
            if self.network_client and self.state in ["online_lobby", "online_room_select", "online_ip_input"]:
                msg = self.network_client.poll_message()
                while msg:
                    ret = self._handle_network_message(msg)
                    if ret:
                        return ret # Transition to game
                    msg = self.network_client.poll_message()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.network_client:
                        self.network_client.disconnect()
                    return {"action": "quit"}

                if event.type == pygame.KEYDOWN:
                    if self.active_input:
                        self._handle_text_input(event)
                    else:
                        if event.key == pygame.K_ESCAPE:
                            if self.state == "main":
                                if self.network_client:
                                    self.network_client.disconnect()
                                return {"action": "quit"}
                            else:
                                self._handle_action("back", has_save)
                        elif event.key == pygame.K_UP:
                            self._move_selection(-1)
                        elif event.key == pygame.K_DOWN:
                            self._move_selection(1)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.buttons:
                                action = self.buttons[self.selected_index]["action"]
                                if self.buttons[self.selected_index]["enabled"]:
                                    payload = self._handle_action(action, has_save)
                                    if payload:
                                        return payload

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check text box clicks
                    clicked_input = False
                    if self.state == "online_ip_input":
                        box_rect = pygame.Rect(WINDOW_WIDTH//2 - 140, WINDOW_HEIGHT//2 - 60, 280, 40)
                        if box_rect.collidepoint(mouse_pos):
                            self.active_input = "ip"
                            clicked_input = True
                    elif self.state == "online_room_select":
                        box_rect = pygame.Rect(WINDOW_WIDTH//2 - 140, WINDOW_HEIGHT//2, 280, 40)
                        if box_rect.collidepoint(mouse_pos):
                            self.active_input = "room_id"
                            clicked_input = True
                    
                    if not clicked_input:
                        self.active_input = None

                    # Check button clicks
                    for i, btn in enumerate(self.buttons):
                        if btn["enabled"] and btn["rect"].collidepoint(mouse_pos):
                            payload = self._handle_action(btn["action"], has_save)
                            if payload:
                                return payload

            # Continuous backspace
            keys = pygame.key.get_pressed()
            if keys[pygame.K_BACKSPACE] and self.active_input:
                self.backspace_timer += clock.get_time()
                if self.backspace_timer > 400: # initial delay
                    self.text_inputs[self.active_input] = self.text_inputs[self.active_input][:-1]
                    self.backspace_timer = 350 # speed up
            else:
                self.backspace_timer = 0

            # Update hover state
            for i, btn in enumerate(self.buttons):
                if btn["enabled"] and btn["rect"].collidepoint(mouse_pos):
                    self.hover_index = i

            self._draw(screen, has_save)
            pygame.display.flip()
            clock.tick(60)

    def _handle_text_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.text_inputs[self.active_input] = self.text_inputs[self.active_input][:-1]
        elif event.key == pygame.K_RETURN:
            # Trigger corresponding button action
            if self.active_input == "ip":
                self._handle_action("connect_ip", False)
            elif self.active_input == "room_id":
                self._handle_action("join_room", False)
            self.active_input = None
        else:
            if len(self.text_inputs[self.active_input]) < 20: # Limit length
                if event.unicode.isprintable():
                    self.text_inputs[self.active_input] += event.unicode

    def _handle_network_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == "ERROR":
            self.error_message = msg.get("message", "Unknown error")
            self.error_timer = pygame.time.get_ticks()
        elif msg_type == "ROOM_CREATED" or msg_type == "ROOM_JOINED":
            self.state = "online_lobby"
            self._build_buttons(False)
        elif msg_type == "GAME_START":
            return {
                "action": "new_game",
                "mode": "online",
                "room_id": self.network_client.room_id,
                "player_color": self.network_client.my_color
            }
        return None

    def _handle_action(self, action, has_save):
        if self.state == "main":
            if action == "new_game":
                self.state = "mode_select"
                self._build_buttons(has_save)
            else:
                return {"action": action}
        elif self.state == "mode_select":
            if action == "back":
                self.state = "main"
                self._build_buttons(has_save)
            elif action == "1p":
                self.state = "difficulty_select"
                self._build_buttons(has_save)
            elif action == "2p":
                return {"action": "new_game", "mode": "2p", "difficulty": None}
            elif action == "online":
                self.state = "online_ip_input"
                self.active_input = "ip"
                self._build_buttons(has_save)
                
        elif self.state == "difficulty_select":
            if action == "back":
                self.state = "mode_select"
                self._build_buttons(has_save)
            else:
                self._temp_difficulty = action
                self.state = "side_select"
                self._build_buttons(has_save)
                
        elif self.state == "side_select":
            if action == "back":
                self.state = "difficulty_select"
                self._build_buttons(has_save)
            else:
                return {
                    "action": "new_game", 
                    "mode": "1p", 
                    "difficulty": self._temp_difficulty,
                    "player_color": action
                }
                
        # ONLINE FLOW
        elif self.state == "online_ip_input":
            if action == "back":
                self.state = "mode_select"
                self._build_buttons(has_save)
            elif action == "connect_ip":
                ip = self.text_inputs["ip"].strip()
                if not ip:
                    ip = "127.0.0.1"
                try:
                    port = 5055
                    if ":" in ip:
                        ip, port_str = ip.split(":")
                        port = int(port_str)
                    
                    if self.network_client.connect(ip, port):
                        self.state = "online_room_select"
                        self.active_input = None
                        self._build_buttons(has_save)
                    else:
                        self.error_message = f"Failed to connect to {ip}:{port}"
                        self.error_timer = pygame.time.get_ticks()
                except Exception as e:
                    self.error_message = f"Invalid connection info: {e}"
                    self.error_timer = pygame.time.get_ticks()
                    
        elif self.state == "online_room_select":
            if action == "back":
                self.network_client.disconnect()
                self.state = "online_ip_input"
                self._build_buttons(has_save)
            elif action == "create_room":
                self.network_client.create_room()
            elif action == "join_room":
                room_code = self.text_inputs["room_id"].strip().upper()
                if room_code:
                    self.network_client.join_room(room_code)
                else:
                    self.error_message = "Please enter a Room ID"
                    self.error_timer = pygame.time.get_ticks()
                    
        elif self.state == "online_lobby":
            if action == "back":
                self.network_client.disconnect()
                self.state = "online_room_select"
                self._build_buttons(has_save)
        return None

    def _build_buttons(self, has_save):
        btn_w = 280
        btn_h = 54
        cx = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 - 10

        if self.state == "main":
            self.buttons = [
                {
                    "label": "Continue", "action": "continue",
                    "enabled": has_save, "rect": pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h),
                },
                {
                    "label": "New Game", "action": "new_game",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 72, btn_w, btn_h),
                },
                {
                    "label": "Quit", "action": "quit",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 144, btn_w, btn_h),
                },
            ]
            self.selected_index = 0 if has_save else 1
            
        elif self.state == "mode_select":
            self.buttons = [
                {
                    "label": "1 Player (vs AI)", "action": "1p",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y - 36, btn_w, btn_h),
                },
                {
                    "label": "Local Multiplayer", "action": "2p",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 36, btn_w, btn_h),
                },
                {
                    "label": "Online Multiplayer", "action": "online",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 108, btn_w, btn_h),
                },
                {
                    "label": "Back", "action": "back",
                    "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 180, btn_w, btn_h),
                },
            ]
            self.selected_index = 0
            
        elif self.state == "room_input":
            self.buttons = [
                {
                    "label": "Cancel",
                    "action": "back",
                    "enabled": True,
                    "rect": pygame.Rect(cx - btn_w // 2, start_y + 150, btn_w, btn_h),
                }
            ]
            self.selected_index = 0
            
        elif self.state == "difficulty_select":
            self.buttons = [
                {"label": "Easy", "action": "easy", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y - 36, btn_w, btn_h)},
                {"label": "Medium", "action": "medium", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 36, btn_w, btn_h)},
                {"label": "Hard", "action": "hard", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 108, btn_w, btn_h)},
                {"label": "Pro", "action": "pro", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 180, btn_w, btn_h)},
                {"label": "Back", "action": "back", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 252, btn_w, btn_h)},
            ]
            self.selected_index = 0

        elif self.state == "side_select":
            self.buttons = [
                {"label": "Play as White", "action": "white", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h)},
                {"label": "Play as Black", "action": "black", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 72, btn_w, btn_h)},
                {"label": "Back", "action": "back", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 144, btn_w, btn_h)},
            ]
            self.selected_index = 0
            
        elif self.state == "online_ip_input":
            self.buttons = [
                {"label": "Connect", "action": "connect_ip", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 20, btn_w, btn_h)},
                {"label": "Back", "action": "back", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 92, btn_w, btn_h)},
            ]
            self.selected_index = 0
            
        elif self.state == "online_room_select":
            self.buttons = [
                {"label": "Create New Room", "action": "create_room", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y - 70, btn_w, btn_h)},
                {"label": "Join Room", "action": "join_room", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 70, btn_w, btn_h)},
                {"label": "Back", "action": "back", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 142, btn_w, btn_h)},
            ]
            self.selected_index = 0
            
        elif self.state == "online_lobby":
            self.buttons = [
                {"label": "Leave Room", "action": "back", "enabled": True, "rect": pygame.Rect(cx - btn_w // 2, start_y + 72, btn_w, btn_h)},
            ]
            self.selected_index = 0
            
        else:
            self.buttons = []

    def _move_selection(self, direction):
        if not self.buttons: return
        n = len(self.buttons)
        idx = self.selected_index
        for _ in range(n):
            idx = (idx + direction) % n
            if self.buttons[idx]["enabled"]:
                self.selected_index = idx
                return

    def _draw(self, screen, has_save):
        screen.fill(COLOR_BG)
        cx = WINDOW_WIDTH // 2

        pygame.draw.rect(screen, COLOR_ACCENT, pygame.Rect(0, 0, WINDOW_WIDTH, 4))

        if self.icon_img:
            title_surf = self.font_title.render("Chess", True, COLOR_TEXT_PRIMARY)
            spacing = 15
            total_w = self.icon_img.get_width() + spacing + title_surf.get_width()
            start_x = cx - total_w // 2
            icon_y = 60 + (title_surf.get_height() - self.icon_img.get_height()) // 2
            screen.blit(self.icon_img, (start_x, icon_y))
            screen.blit(title_surf, (start_x + self.icon_img.get_width() + spacing, 60))
        else:
            title_surf = self.font_title.render("♚ Chess", True, COLOR_TEXT_PRIMARY)
            screen.blit(title_surf, (cx - title_surf.get_width() // 2, 60))

        subtitle_text = "A classic chess experience"
        if self.state == "mode_select": subtitle_text = "Select Game Mode"
        elif self.state == "difficulty_select": subtitle_text = "Select AI Difficulty"
        elif self.state == "side_select": subtitle_text = "Select Your Side"
        elif self.state == "online_ip_input": subtitle_text = "Connect to Server"
        elif self.state == "online_room_select": subtitle_text = "Multiplayer Rooms"
        elif self.state == "online_lobby": subtitle_text = "Lobby Waiting Room"

        subtitle_surf = self.font_subtitle.render(subtitle_text, True, COLOR_TEXT_SECONDARY)
        screen.blit(subtitle_surf, (cx - subtitle_surf.get_width() // 2, 130))

        line_w = 200
        pygame.draw.line(screen, COLOR_BORDER, (cx - line_w // 2, 160), (cx + line_w // 2, 160), 2)

        # Draw Inputs
        start_y = WINDOW_HEIGHT // 2 - 10
        if self.state == "online_ip_input":
            self._draw_text_box(screen, "IP Address:", self.text_inputs["ip"], (cx - 140, start_y - 60), self.active_input == "ip")
        elif self.state == "online_room_select":
            self._draw_text_box(screen, "Enter Room ID to Join:", self.text_inputs["room_id"], (cx - 140, start_y), self.active_input == "room_id")
        elif self.state == "online_lobby":
            rid = self.network_client.room_id if self.network_client else "???"
            txt = self.font_button.render(f"Room ID: {rid}", True, COLOR_TEXT_PRIMARY)
            screen.blit(txt, (cx - txt.get_width()//2, start_y - 30))
            
            wait_txt = self.font_subtitle.render("Waiting for opponent to join...", True, COLOR_ACCENT)
            screen.blit(wait_txt, (cx - wait_txt.get_width()//2, start_y + 10))

        # Buttons
        for i, btn in enumerate(self.buttons):
            is_selected = (i == self.selected_index and not self.active_input) or (i == self.hover_index)
            self._draw_button(screen, btn, is_selected)

        # Error msg
        if self.error_message:
            err_surf = self.font_error.render(self.error_message, True, (255, 80, 80))
            screen.blit(err_surf, (cx - err_surf.get_width() // 2, WINDOW_HEIGHT - 70))

        hint = "↑↓ Navigate  •  Enter Select  •  ESC Quit"
        hint_surf = self.font_hint.render(hint, True, COLOR_TEXT_SECONDARY)
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, WINDOW_HEIGHT - 40))

    def _draw_text_box(self, screen, label, value, topleft, is_active):
        cx = WINDOW_WIDTH // 2
        
        lbl_surf = self.font_hint.render(label, True, COLOR_TEXT_SECONDARY)
        screen.blit(lbl_surf, (topleft[0], topleft[1] - 20))
        
        rect = pygame.Rect(topleft[0], topleft[1], 280, 40)
        
        # Cursor blink logic
        if is_active and (pygame.time.get_ticks() % 1000 < 500):
            display_val = value + "|"
        else:
            display_val = value
            
        color = COLOR_ACCENT if is_active else COLOR_BORDER
        pygame.draw.rect(screen, COLOR_PANEL_BG, rect, border_radius=4)
        pygame.draw.rect(screen, color, rect, 2, border_radius=4)
        
        txt_surf = self.font_input.render(display_val, True, COLOR_TEXT_PRIMARY)
        screen.blit(txt_surf, (rect.x + 10, rect.y + 8))

    def _draw_button(self, screen, btn, is_selected):
        rect = btn["rect"]
        enabled = btn["enabled"]

        if not enabled:
            bg_color = (50, 48, 45)
            text_color = (100, 100, 100)
            border_color = (60, 58, 55)
        elif is_selected:
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
        lx = rect.centerx - label_surf.get_width() // 2
        ly = rect.centery - label_surf.get_height() // 2
        screen.blit(label_surf, (lx, ly))
