import pygame
from core.board import Board
from core.move import Move
from core.game_state import GameState
from core.rules import Rules
from core.timer import Timer
from core.save_manager import SaveManager
from core.sound_manager import SoundManager
from controllers.turn_controller import TurnController
from ui.renderer import Renderer
from ui.input_handler import InputHandler
from ui.timer_ui import TimerUI
from ui.menu import MainMenu
from ui.pause_menu import PauseMenu
from ui.promotion_dialog import PromotionDialog
from ui.animation import Animation
from network.client import NetworkClient
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, COLOR_BG


class GameController:
    """
    Main game controller that bridges the core logic and UI rendering.
    Manages the full app lifecycle: Menu → Playing → Paused → Menu.
    """
    
    def __init__(self):
        """Initialize all game components and set up the game window."""
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()
        
        # Initialize core components
        self.board = Board()
        self.rules = Rules()
        self.game_state = GameState(self.board, rules=self.rules)
        
        # Initialize timer
        self.timer = Timer(white_time_seconds=300.0, black_time_seconds=300.0, increment_seconds=0.0)
        
        self.turn_controller = TurnController(
            game_state=self.game_state,
            rules=self.rules,
            board=self.board,
            timer=self.timer
        )
        
        # Initialize UI components
        self.renderer = Renderer()
        self.timer_ui = TimerUI(self.timer, self.renderer.font_heading)
        # Update renderer with timer_ui instance
        self.renderer.timer_ui = self.timer_ui
        self.input_handler = InputHandler()
        self.main_menu = MainMenu()
        self.pause_menu = PauseMenu()
        self.promotion_dialog = PromotionDialog(self.renderer.piece_ui)
        self.animation = Animation()
        self.network_client = NetworkClient()
        self.online_mode = False
        self.my_color = None
        
        # Initialize Sound Manager
        self.sound_manager = SoundManager()
        self.sound_manager.play_background_music()
        
        # Game state flags
        self.running = True
        
        # App state: "menu", "playing", "paused"
        self.app_state = "menu"
        
        # Clock settings for reset
        self.clock_enabled = False
        self.time_per_player = 300.0  # Default: 5 minutes
        
        # AI settings for reset
        self.ai_agent = None
        self.ai_color = None

        # Network settings
        self.network_client = None
        self.is_online_game = False
        self.online_color = None
        self.online_room_id = None
        self.waiting_for_opponent = False
        self.is_receiving_network_move = False

        # Online promotion flow flags
        self.is_promoting = False
        self.pending_promotion_move = None
        self.waiting_for_server = False
        
        # Communication action flags
        self.draw_offer_cooldown = 0.0  # Cooldown timer after sending draw offer
        self.is_showing_draw_dialog = False  # Draw offer dialog is active
        self.pending_draw_offer_from_opponent = False  # We received a draw offer, waiting for response

    def run(self):
        """
        Main application loop.
        
        Manages transitions between Menu → Playing → Paused states.
        """
        while self.running:
            if self.app_state == "menu":
                self._run_menu()
            elif self.app_state == "playing":
                self._run_game()
            elif self.app_state == "paused":
                self._run_pause()
        
        # Clean up
        self.sound_manager.cleanup()
        pygame.quit()

    # ==================== Menu State ====================

    def _run_menu(self):
        """Show the main menu and handle user choice."""
        has_save = SaveManager.has_save()
        payload = self.main_menu.show(self.screen, self.clock, has_save=has_save, network_client=self.network_client)
        
        if not payload:
            return

        action = payload.get("action")
        
        if action == "new_game":
            mode = payload.get("mode", "2p")
            difficulty = payload.get("difficulty")
            player_color = payload.get("player_color", 'white')
            
            if mode == "online":
                self.online_mode = True
                self.my_color = player_color
                self._start_new_game(mode="online", player_color=player_color)
            else:
                self.online_mode = False
                self.my_color = None
                self._start_new_game(mode, difficulty, player_color)
            self.app_state = "playing"
        elif action == "continue":
            success = self._load_saved_game()
            if success:
                self.app_state = "playing"
            else:
                # Failed to load, stay in menu
                print("Failed to load saved game, staying in menu.")
        elif action == "quit":
            self.running = False

    # ==================== Playing State ====================

    def _setup_online_game(self, payload):
        """Initialize sockets and wait for connection."""
        from core.network_client import NetworkClient
        self.is_online_game = True
        self.network_client = NetworkClient()
        if not self.network_client.connect():
            print("Could not connect to online server 127.0.0.1:8888")
            return
            
        self._reset_game()
        SaveManager.delete_save()
        self.sound_manager.play_game_start()
        
        self.waiting_for_opponent = True
        self.app_state = "playing"
        
        online_action = payload.get("online_action")
        if online_action == "create":
            self.network_client.send({"action": "create_room"})
        elif online_action == "join":
            room_id = payload.get("room_id")
            self.network_client.send({"action": "join_room", "room_id": room_id})

    def _handle_network_events(self):
        """Process incoming socket events if online."""
        if not self.is_online_game or not self.network_client:
            return
            
        for event in self.network_client.get_events():
            action = (event.get("action") or "").lower()
            if action == "room_created":
                self.online_room_id = event.get("room_id")
                self.online_color = "white"
                self.input_handler.reversed_view = False
            elif action == "room_joined":
                self.online_room_id = event.get("room_id")
                self.online_color = event.get("color", "black")
                self.input_handler.reversed_view = (self.online_color == "black")
                self.waiting_for_opponent = False
            elif action == "opponent_joined":
                self.waiting_for_opponent = False
            elif action in {"sync", "move"}:
                move_data = event.get("move") or event.get("data")
                start_pos = None
                end_pos = None
                network_promotion = None

                # Preferred compact format: e7e8Q
                if isinstance(move_data, str):
                    try:
                        start_pos, end_pos, network_promotion = Move.from_network_format(move_data)
                    except ValueError:
                        start_pos = None

                # Backward compatibility with start/end fields
                if start_pos is None:
                    if event.get("start") is not None and event.get("end") is not None:
                        start_pos = tuple(event.get("start"))
                        end_pos = tuple(event.get("end"))
                        network_promotion = event.get("promotion")

                if start_pos is None or end_pos is None:
                    continue

                # Timer synchronization from server packet (authoritative)
                if event.get("white_time") is not None and event.get("black_time") is not None:
                    self.timer.sync(event.get("white_time"), event.get("black_time"))

                # Apply move only after server event arrives
                self.is_receiving_network_move = True
                self._attempt_move(start_pos, end_pos, network_promotion)
                self.is_receiving_network_move = False

                # Server confirmed a move, unlock client input
                self.waiting_for_server = False
                self.is_promoting = False
                self.pending_promotion_move = None
                self.promotion_dialog.close()
            elif action == "time_out":
                winner = event.get("winner")
                if winner in {"white", "black"}:
                    self.game_state.timeout_winner = winner
                    self.turn_controller.game_over = True
                    self.turn_controller.game_over_reason = "timeout"
                    self.turn_controller.winner = winner
                self.waiting_for_server = False
            elif action == "opponent_disconnected":
                self._handle_game_over({'status': 'opponent_disconnected', 'message': 'Opponent Disconnected'})
            elif action == "resign":
                # Opponent resigned
                opponent = event.get("player")
                if opponent == self.online_color:
                    # This shouldn't happen (we wouldn't receive our own resignation)
                    pass
                else:
                    # Opponent resigned, we win
                    loser = "white" if opponent == "white" else "black"
                    self.game_state.resigned_player = loser
                    self.turn_controller.game_over = True
                    self.turn_controller.game_over_reason = "resignation"
                    self.turn_controller.winner = "black" if loser == "white" else "white"
            elif action == "offer_draw":
                # Opponent offers a draw
                self.is_showing_draw_dialog = True
                self.pending_draw_offer_from_opponent = True
                self.draw_offer_dialog.open()
            elif action == "draw_declined":
                # Our draw offer was declined
                self.action_panel_ui.set_draw_offer_cooldown(10.0)  # 10 second cooldown
                print("Opponent declined the draw offer.")
            elif action == "draw_accepted":
                # Both players agreed to draw
                self.game_state.is_draw_agreed = True
                self.turn_controller.game_over = True
                self.turn_controller.game_over_reason = "draw_agreed"
            elif action == "error":
                print(f"Server Error: {event.get('message')}")
                if self.waiting_for_opponent:
                    # Return to menu if join fails
                    self.network_client.disconnect()
                    self.app_state = "menu"

    def _run_game(self):
        """
        Main game loop following the Input → Update → Render pattern.
        """
        # Check if AI should move first (if AI is white)
        if self.turn_controller._is_ai_turn():
            self.turn_controller._trigger_ai()
        
        # Start the timer when game begins
        if self.timer:
            self.timer.start()
        
        while self.running and self.app_state == "playing":
            # Network processing
            if self.online_mode and self.network_client:
                self._process_network_messages()
                
            # Input: Process all events
            self._handle_events()
            
            # Check for pending AI moves and execute them
            self._check_and_execute_ai_move()
            
            # Update: Timer tick (decrement current player's time)
            if self.timer:
                self.timer.tick(delta_time)
                self.timer_ui.tick(delta_time)
            
            # Update: Action panel cooldowns (for draw offer spamming prevention)
            self.action_panel_ui.tick(delta_time)
            
            # Update: Sync timer values from turn_controller to game_state
            self._update_timers()
            
            # Render: Draw the current game state
            self._render()
    
    def _handle_events(self):
        """Process all input events from the player."""
        for event in pygame.event.get():
            # Window close event — auto-save and quit
            if event.type == pygame.QUIT:
                self._auto_save_and_quit()
                return
            
            # Keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Open pause menu instead of quitting
                    self._pause_game()
                    return
                elif event.key == pygame.K_r:
                    # Only allow reset if game is over
                    if self.game_state.is_game_over:
                        self._start_new_game()
            
            # Mouse motion for dialog hover effects
            if event.type == pygame.MOUSEMOTION:
                if self.is_showing_draw_dialog:
                    self.draw_offer_dialog.handle_mousemotion(event.pos)
            
            # Don't process moves if game is over
            if self.game_state.is_game_over:
                continue

            # Draw offer dialog is active: only process dialog clicks
            if self.is_showing_draw_dialog:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    dialog_response = self.draw_offer_dialog.handle_click(event.pos)
                    if dialog_response == "ACCEPT_DRAW":
                        self._handle_accept_draw()
                    elif dialog_response == "DECLINE_DRAW":
                        self._handle_decline_draw()
                continue

            # Promotion selection phase: only process promotion popup clicks
            if self.is_promoting:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    selected_code = self.promotion_dialog.get_selected_piece(event.pos)
                    if selected_code:
                        self._finalize_pending_promotion(selected_code)
                continue

            # While waiting for server confirmation in online mode, block board input
            if self.is_online_game and self.waiting_for_server:
                continue
            
            # Action panel button clicks (online only)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_online_game:
                    button_signal = self.action_panel_ui.handle_click(event.pos)
                    if button_signal == "BTN_RESIGN":
                        self._handle_resign_click()
                    elif button_signal == "BTN_OFFER_DRAW":
                        self._handle_offer_draw_click()
            
            is_online_opponent_turn = self.online_mode and self.turn_controller.current_player != self.my_color
            
            # Mouse events (handled by InputHandler)
            action = self.input_handler.handle_event(event, self.game_state, self.turn_controller, is_online_opponent_turn)
            
            if action is not None:
                self._process_action(action)
    
    def _process_action(self, action):
        """
        Process an action returned by the InputHandler.
        
        Args:
            action: Dict with type and relevant data
                    {"type": "move", "start": (r,c), "end": (r,c)}
                    {"type": "deselect"}
        """
        if action["type"] == "move":
            self._attempt_move(action["start"], action["end"])
        
        elif action["type"] == "deselect":
            # Clear any selection (already handled by InputHandler)
            pass
    
    def _attempt_move(self, start_pos, end_pos, remote_promotion=None, is_network_move=False):
        """
        Attempt to execute a move from start_pos to end_pos.
        """
        last_move_index = len(self.game_state.move_log)
        
        promotion_piece = remote_promotion
        piece = self.game_state.board[start_pos[0]][start_pos[1]]
        if piece and piece.name == "pawn" and not is_network_move:
            end_row = end_pos[0]
            if end_row == 0 or end_row == 7:
                is_ai_turn = (self.turn_controller.ai_enabled and 
                              self.turn_controller.ai_color == self.game_state.current_turn)
                if not is_ai_turn:
                    self._render()  
                    promotion_piece = self.promotion_dialog.show(
                        self.screen, self.clock, piece.color, end_pos[1]
                    )
        
        move_successful = self.game_state.process_move(start_pos, end_pos, promotion_piece)
        
        # Send draw offer packet
        self.network_client.send({
            "action": "OFFER_DRAW",
            "player": self.online_color
        })
        
        # Set cooldown to prevent spam
        self.action_panel_ui.set_draw_offer_cooldown(10.0)
    
    def _handle_accept_draw(self):
        """
        Player accepted the draw offer from opponent.
        
        Send acceptance to server and end game with draw result.
        """
        if not self.is_online_game or not self.network_client:
            return
        
        # Send acceptance packet
        self.network_client.send({
            "action": "ACCEPT_DRAW",
            "player": self.online_color
        })
        
        # Close dialog and wait for server game-over confirmation
        self.is_showing_draw_dialog = False
        self.pending_draw_offer_from_opponent = False
        self.draw_offer_dialog.close()
        self.waiting_for_server = True
    
    def _handle_decline_draw(self):
        """
        Player declined the draw offer from opponent.
        
        Send declination to server and resume game.
        """
        if not self.is_online_game or not self.network_client:
            return
        
        # Send declination packet
        self.network_client.send({
            "action": "DECLINE_DRAW",
            "player": self.online_color
        })
        
        # Close dialog and resume game
        self.is_showing_draw_dialog = False
        self.pending_draw_offer_from_opponent = False
        self.draw_offer_dialog.close()

    @staticmethod
    def _promotion_code_to_piece_class(code):
        promo_map = {
            "Q": Queen,
            "R": Rook,
            "B": Bishop,
            "N": Knight,
        }
        if code is None:
            return None
        return promo_map.get(str(code).upper())

    @staticmethod
    def _piece_class_to_promotion_code(piece_cls):
        if piece_cls is None:
            return None
        name = getattr(piece_cls, "__name__", "")
        reverse_map = {
            "Queen": "Q",
            "Rook": "R",
            "Bishop": "B",
            "Knight": "N",
        }
        return reverse_map.get(name)

    def _queue_promotion_dialog(self, start_pos, end_pos, color):
        """Enter promotion selection state without modifying board state."""
        self.is_promoting = True
        self.pending_promotion_move = {
            "start": start_pos,
            "end": end_pos,
            "color": color,
        }
        self.promotion_dialog.open(
            color=color,
            col=end_pos[1],
            row=end_pos[0],
            reversed_view=self.input_handler.reversed_view,
        )

    def _send_online_move_request(self, start_pos, end_pos, promotion_code=None):
        """Send move request to server in compact and legacy-compatible formats."""
        move_obj = Move(start_pos, end_pos, self.game_state.board, promotion_piece=promotion_code)
        move_str = move_obj.to_network_format()

        # Primary protocol (compact string form)
        self.network_client.send({
            "action": "MOVE",
            "data": move_str,
        })

        # Backward compatibility payload for current relay servers
        self.network_client.send({
            "action": "move",
            "start": start_pos,
            "end": end_pos,
            "promotion": promotion_code,
            "move": move_str,
        })

    def _finalize_pending_promotion(self, selected_code):
        """Finalize selected promotion and continue according to game mode."""
        if not self.pending_promotion_move:
            self.is_promoting = False
            self.promotion_dialog.close()
            return

        start_pos = self.pending_promotion_move["start"]
        end_pos = self.pending_promotion_move["end"]

        self.is_promoting = False
        self.promotion_dialog.close()

        if self.is_online_game and not self.is_receiving_network_move:
            self._send_online_move_request(start_pos, end_pos, selected_code)
            self.waiting_for_server = True
            self.pending_promotion_move = None
            return

        promotion_piece = self._promotion_code_to_piece_class(selected_code)
        self.pending_promotion_move = None
        self._attempt_move(start_pos, end_pos, promotion_piece)

    def _apply_confirmed_move(self, start_pos, end_pos, promotion_piece=None):
        """Apply a move that is already authorized (offline or server-confirmed online)."""
        last_move_index = len(self.game_state.move_log)

        move_successful = self.game_state.process_move(start_pos, end_pos, promotion_piece)

        if move_successful:
            if not is_network_move and self.online_mode and self.network_client:
                self.network_client.send_move(start_pos, end_pos, promotion_piece)
                
            if last_move_index < len(self.game_state.move_log):
                last_move = self.game_state.move_log[-1]
                self._play_move_sound(last_move)

            self.rules.update_position_history(self.board)
            turn_result = self.turn_controller.complete_turn(move_successful=True)

            if turn_result['game_over']:
                self._handle_game_over(turn_result['game_status'])
            else:
                game_status = turn_result.get('game_status', {})
                if game_status.get('status') == 'check':
                    self.sound_manager.play_check()

            if turn_result.get('ai_turn', False):
                self._trigger_ai_move()
            return True

        self.sound_manager.play_illegal_move()
        return False
    
    def _attempt_move(self, start_pos, end_pos, network_promotion=None):
        """
        Attempt to execute a move from start_pos to end_pos.
        
        This is the core bridge function that:
        1. Asks the core logic to validate and execute the move
        2. Updates turn state if successful
        3. Triggers UI updates
        
        Args:
            start_pos: (row, col) starting position
            end_pos: (row, col) ending position
        """
        # Local player in online mode: never mutate board before server confirmation.
        if self.is_online_game and not self.is_receiving_network_move:
            if self.waiting_for_opponent or self.waiting_for_server:
                return
            if self.game_state.current_turn != self.online_color:
                return

            promotion_code = None
            if network_promotion is not None:
                if isinstance(network_promotion, str):
                    promotion_code = network_promotion.upper()
                else:
                    promotion_code = self._piece_class_to_promotion_code(network_promotion)

            piece = self.game_state.board[start_pos[0]][start_pos[1]]
            is_ai_turn = (
                self.turn_controller.ai_enabled and
                self.turn_controller.ai_color == self.game_state.current_turn
            )

            if self.rules.is_promotion_move(self.board, start_pos, end_pos) and promotion_code is None:
                if is_ai_turn:
                    promotion_code = "Q"
                else:
                    self._queue_promotion_dialog(start_pos, end_pos, piece.color if piece else self.game_state.current_turn)
                    return

            self._send_online_move_request(start_pos, end_pos, promotion_code)
            self.waiting_for_server = True
            return

        # Offline or server-authorized online move: apply immediately.
        promotion_piece = network_promotion

        # For offline human promotion, collect piece choice first.
        if not self.is_online_game:
            piece = self.game_state.board[start_pos[0]][start_pos[1]]
            is_ai_turn = (
                self.turn_controller.ai_enabled and
                self.turn_controller.ai_color == self.game_state.current_turn
            )
            if self.rules.is_promotion_move(self.board, start_pos, end_pos) and promotion_piece is None:
                if is_ai_turn:
                    promotion_piece = Queen
                else:
                    self._queue_promotion_dialog(start_pos, end_pos, piece.color if piece else self.game_state.current_turn)
                    return

        # Convert promotion token from network to piece class if needed.
        if isinstance(promotion_piece, str):
            promotion_piece = self._promotion_code_to_piece_class(promotion_piece)

        self._apply_confirmed_move(start_pos, end_pos, promotion_piece)
    
    def _handle_game_over(self, game_status):
        """
        Handle game over scenarios.
        
        Args:
            game_status: Dict containing status info (checkmate, stalemate, draw, etc.)
        """
        status_type = game_status.get('status', 'unknown')
        message = game_status.get('message', 'Game over')
        
        if getattr(self, "online_mode", False) and getattr(self, "my_color", None):
            winner = game_status.get('winner')
            if winner == self.my_color:
                message = "Bạn đã thắng!"
            elif winner and winner != self.my_color:
                message = "Bạn đã thua!"
            elif status_type in ["draw", "stalemate", "threefold_repetition", "fifty_move_rule", "insufficient_material"]:
                message = "Hòa!"

        # Play game end sound
        self.sound_manager.play_game_end()
        
        # Log game over for debugging
        print(f"Game Over: {message} (Status: {status_type})")
        
        # Record popup to be shown during render
        self.end_game_popup = {"status": status_type, "message": message}
        
        # Delete save file when game is over
        SaveManager.delete_save()
    
    def _play_move_sound(self, last_move_dict):
        """
        Play the appropriate sound based on the move type.
        
        Args:
            last_move_dict: Dictionary containing move information from move_log
        """
        # Get the piece that was moved
        piece = last_move_dict.get('piece')
        start = last_move_dict.get('start')
        end = last_move_dict.get('end')
        captured = last_move_dict.get('captured')
        
        # Check for promotion (pawn reaching the last rank)
        if piece and piece.name == 'pawn':
            end_row = end[0]
            if end_row == 0 or end_row == 7:
                self.sound_manager.play_promotion()
                return
        
        # Check for castling (king moving 2 squares horizontally)
        if piece and piece.name == 'king':
            start_col = start[1]
            end_col = end[1]
            if abs(end_col - start_col) == 2:
                self.sound_manager.play_castle()
                return
        
        # Check for capture
        if captured is not None:
            self.sound_manager.play_capture()
            return
        
        # Check for en passant (pawn diagonal move with no piece captured at destination)
        if piece and piece.name == 'pawn':
            start_col = start[1]
            end_col = end[1]
            if start_col != end_col and captured is None:
                # This is en passant
                self.sound_manager.play_capture()
                return
        
        # Normal move
        self.sound_manager.play_move()

    
    def _update_timers(self):
        """
        Update game_state timer values from timer object.
        
        This syncs the dynamic timer values so the renderer can display them.
        """
        if self.timer:
            self.game_state.white_time = self.timer.white_time
            self.game_state.black_time = self.timer.black_time
            
            # Check for timeout and update game state
            if self.timer.is_timeout():
                timed_out_player = self.timer.is_timeout()
                self.game_state.timeout_winner = 'black' if timed_out_player == 'white' else 'white'
            else:
                self.game_state.timeout_winner = None
            
            # Play warning sound when time drops below 60 seconds
            if self.timer.white_time < 60 and self.timer.white_time > 0:
                self.sound_manager.play_ten_second_warning('white')
            if self.timer.black_time < 60 and self.timer.black_time > 0:
                self.sound_manager.play_ten_second_warning('black')
        elif self.turn_controller.clock_enabled:
            # Fallback to legacy system if no timer
            white_time = self.turn_controller.get_time_remaining('white')
            black_time = self.turn_controller.get_time_remaining('black')
            
            self.game_state.white_time = white_time
            self.game_state.black_time = black_time
            self.game_state.timeout_winner = self.turn_controller.winner if self.turn_controller.game_over_reason == 'timeout' else None
            
            # Play warning sound when time drops below 60 seconds
            if white_time < 60 and white_time > 0:
                self.sound_manager.play_ten_second_warning('white')
            if black_time < 60 and black_time > 0:
                self.sound_manager.play_ten_second_warning('black')
    
    def _check_and_execute_ai_move(self):
        """
        Check for pending AI moves and execute them.
        
        This is called every frame in the main game loop to process AI moves
        as soon as they're ready.
        """
        if self.game_state.pending_ai_move is not None:
            ai_move = self.game_state.pending_ai_move
            self.game_state.pending_ai_move = None
            
            # Execute the AI's chosen move
            start_pos = (ai_move.start_row, ai_move.start_col)
            end_pos = (ai_move.end_row, ai_move.end_col)
            
            # Use pygame.time.delay to make AI move visible (optional)
            pygame.time.delay(300)  # 300ms delay so players can see the move
            
            self._attempt_move(start_pos, end_pos)
    
    def _trigger_ai_move(self):
        """
        Trigger AI to generate its move.
        
        This is called after a turn completes and it's the AI's turn.
        The AI move will be executed in the next frame by _check_and_execute_ai_move().
        """
        # The turn_controller._trigger_ai() has already been called
        # and set pending_ai_move, so we don't need to do anything here
        pass
    
    def _render(self):
        """
        Render the complete game frame.
        """
        # Clear screen
        self.screen.fill(COLOR_BG)
        
        # Draw everything (board, pieces, highlights, sidebar, overlays)
        self.renderer.draw(self.screen, self.game_state, self.input_handler, self)
        
        if hasattr(self, 'end_game_popup') and self.end_game_popup:
            self._draw_popup(self.end_game_popup["message"])
            
        pygame.display.flip()

    def _draw_popup(self, message):
        font = pygame.font.SysFont("Segoe UI", 36, bold=True)
        text_surf = font.render(message, True, (255, 255, 255))
        rect_w = text_surf.get_width() + 60
        rect_h = 100
        cx, cy = self.screen.get_width() // 2, self.screen.get_height() // 2
        
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        popup_rect = pygame.Rect(cx - rect_w//2, cy - rect_h//2, rect_w, rect_h)
        pygame.draw.rect(self.screen, (40, 40, 45), popup_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 215, 0), popup_rect, 3, border_radius=12)
        self.screen.blit(text_surf, (cx - text_surf.get_width()//2, cy - text_surf.get_height()//2))

    def _process_network_messages(self):
        msg = self.network_client.poll_message()
        while msg:
            msg_type = msg.get("type")
            if msg_type == "MOVE":
                start_pos = tuple(msg.get("start"))
                end_pos = tuple(msg.get("end"))
                promotion = msg.get("promotion")
                
                piece = self.game_state.board[start_pos[0]][start_pos[1]]
                if piece:
                    self.animation.animate_move(
                        self.screen, self.renderer.board_ui, self.renderer.piece_ui,
                        piece, start_pos, end_pos, self.game_state.board,
                        self.game_state, self.clock, 
                        draw_callback=lambda: self.renderer.draw_player_panels(self.screen, self.game_state, self)
                    )
                
                self._attempt_move(start_pos, end_pos, remote_promotion=promotion, is_network_move=True)
            elif msg_type == "OPPONENT_DISCONNECTED":
                # Only show if not game over already
                if not self.game_state.is_game_over:
                    self._handle_game_over({"status": "disconnect", "message": "Đối thủ đã mất kết nối"})
                    
            msg = self.network_client.poll_message()

    # ==================== Pause State ====================

    def _pause_game(self):
        """Transition to pause state: stop clock and show pause menu."""
        # Pause the clock
        if self.turn_controller.clock_enabled:
            self.turn_controller._stop_clock(self.turn_controller.current_player)
        
        self.app_state = "paused"

    def _run_pause(self):
        """Show the pause menu overlay and handle user action."""
        action = self.pause_menu.show(
            self.screen, self.clock,
            self.game_state, self.renderer, self.input_handler
        )
        
        if action == "resume":
            # Resume clock and return to playing
            if self.turn_controller.clock_enabled:
                self.turn_controller._start_clock(self.turn_controller.current_player)
            self.app_state = "playing"
        elif action == "save_quit":
            # Save game and return to menu
            if not self.game_state.is_game_over:
                SaveManager.save_game(self)
            self.app_state = "menu"

    # ==================== Save/Load ====================

    def _auto_save_and_quit(self):
        """Auto-save (if game is in progress) and quit the application."""
        if not self.game_state.is_game_over:
            # Stop clock before saving so time is accurate
            if self.turn_controller.clock_enabled:
                self.turn_controller._stop_clock(self.turn_controller.current_player)
            SaveManager.save_game(self)
            print("Game auto-saved on exit.")
        self.app_state = "quit"
        if getattr(self, "network_client", None):
            self.network_client.disconnect()

    def _load_saved_game(self):
        """
        Load a saved game and restore state.
        
        Returns:
            bool: True if load was successful
        """
        state = SaveManager.load_game()
        if state is None:
            return False
        
        try:
            SaveManager.restore_game_state(self, state)
            return True
        except Exception as e:
            print(f"Error restoring game state: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _restore_ai(self, ai_agent_type, ai_color):
        """
        Restore AI agent from saved type name.
        
        Args:
            ai_agent_type: Class name of the AI agent (e.g., "MinimaxAgent")
            ai_color: Color the AI plays ('white' or 'black')
        """
        from agents import RandomAgent, MinimaxAgent, MCTSAgent
        
        agent_map = {
            "RandomAgent": lambda: RandomAgent("Easy Bot"),
            "MinimaxAgent": lambda: MinimaxAgent(name="Minimax Bot", depth=3),
            "MCTSAgent": lambda: MCTSAgent(think_time=3.0, max_rollout_depth=30)
        }
        
        factory = agent_map.get(ai_agent_type)
        if factory:
            agent = factory()
            self.enable_ai(ai_color=ai_color, ai_agent=agent)
            
            # Check if it's AI's turn after restore
            if self.turn_controller._is_ai_turn():
                self.turn_controller._trigger_ai()

    # ==================== Game Setup ====================
    
    def _start_new_game(self, mode=None, difficulty=None, player_color="white"):
        """Start a fresh new game."""
        
        # If explicitly passed from menu, update the controller's AI settings
        if mode == "1p" and difficulty:
            from agents import RandomAgent, MinimaxAgent, MCTSAgent, DLAgent
            # Determine AI color (opposite of player color)
            self.ai_color = 'black' if player_color == 'white' else 'white'
            
            if difficulty == "easy":
                self.ai_agent = RandomAgent("Easy")
            elif difficulty == "medium":
                self.ai_agent = MCTSAgent(name="Medium", think_time=3.5, max_rollout_depth=30)
            elif difficulty == "hard":
                self.ai_agent = DLAgent(
                    model_path="ai/DL/trained_model/best_chess_model.keras",
                    max_depth=4,
                    beam_width=5,
                    name="Hard"
                )
            elif difficulty == "pro":
                self.ai_agent = MinimaxAgent(name="Pro", depth=3)
            
            # Update input handler's reversed view (reverse if player is black)
            self.input_handler.reversed_view = (player_color == 'black')
        elif mode == "2p":
            self.ai_agent = None
            self.ai_color = None
            self.input_handler.reversed_view = False
        elif mode == "online":
            self.ai_agent = None
            self.ai_color = None
            self.input_handler.reversed_view = (player_color == 'black')
            
        self.end_game_popup = None
        self._reset_game()
        # Delete any existing save since we're starting fresh
        SaveManager.delete_save()
        
        # Play game start sound
        self.sound_manager.play_game_start()
        # Reset time warning tracking
        self.sound_manager.reset_time_warnings()

    def _reset_game(self):
        """
        Reset the game to initial state.
        
        This creates fresh instances of all game components,
        effectively starting a new game.
        """
        # Reinitialize core components
        self.board = Board()
        self.rules = Rules()
        self.game_state = GameState(self.board, rules=self.rules)
        
        # Reset timer
        self.timer.reset(white_time=self.time_per_player, black_time=self.time_per_player)
        self.timer.stop()
        
        self.turn_controller = TurnController(
            game_state=self.game_state,
            rules=self.rules,
            board=self.board,
            timer=self.timer
        )
        
        # Re-enable clock if it was enabled before
        if self.clock_enabled:
            self.turn_controller.enable_clock(self.time_per_player)
        
        # Re-enable AI if it was enabled before
        if self.ai_agent is not None:
            self.ai_agent.reset()  # Reset agent state
            self.turn_controller.enable_ai(self.ai_color, self.ai_agent.get_move)
            # Trigger AI if it's AI's turn after reset (e.g., if AI is white)
            if self.turn_controller._is_ai_turn():
                self.turn_controller._trigger_ai()
        
        # Clear input handler state
        self.input_handler.reset()

        # Reset promotion/network waiting state
        self.is_promoting = False
        self.pending_promotion_move = None
        self.waiting_for_server = False
        self.promotion_dialog.close()
        
        # Reset communication action state
        self.draw_offer_cooldown = 0.0
        self.is_showing_draw_dialog = False
        self.pending_draw_offer_from_opponent = False
        self.action_panel_ui.reset()
        self.draw_offer_dialog.close()
    
    def enable_clock(self, time_per_player=300.0):
        """
        Enable the game clock with specified time control.
        
        Args:
            time_per_player: Time in seconds for each player (default: 5 minutes)
        """
        self.clock_enabled = True
        self.time_per_player = time_per_player
        self.turn_controller.enable_clock(time_per_player)
    
    def enable_ai(self, ai_color, ai_agent=None, ai_callback=None):
        """
        Enable AI for a specific color.
        
        You can pass either an agent object or a callback function:
        - Agent object: game.enable_ai('black', ai_agent=RandomAgent())
        - Callback function: game.enable_ai('black', ai_callback=my_callback)
        
        Args:
            ai_color: 'white' or 'black'
            ai_agent: An agent object (must have get_move method)
            ai_callback: Function to call for AI moves (if not using agent)
        """
        if ai_agent is not None:
            # Store agent for reset functionality
            self.ai_agent = ai_agent
            self.ai_color = ai_color
            callback = ai_agent.get_move
        elif ai_callback is not None:
            callback = ai_callback
            self.ai_color = ai_color
        else:
            raise ValueError("Must provide either ai_agent or ai_callback")
        
        # Update input handler's reversed view if AI is white (player is black)
        self.input_handler.reversed_view = (ai_color == 'white')
        
        self.turn_controller.enable_ai(ai_color, callback)
    
    def get_game_info(self):
        """
        Get current game information.
        
        Returns:
            dict: Current game state information
        """
        return {
            'current_turn': self.game_state.current_turn,
            'move_count': len(self.game_state.move_log),
            'is_checkmate': self.game_state.is_checkmate,
            'is_draw': self.game_state.is_draw,
            'game_over': self.game_state.is_game_over,
            'turn_info': self.turn_controller.get_turn_info()
        }
