import pygame
from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from core.save_manager import SaveManager
from core.sound_manager import SoundManager
from controllers.turn_controller import TurnController
from ui.renderer import Renderer
from ui.input_handler import InputHandler
from ui.menu import MainMenu
from ui.pause_menu import PauseMenu
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
        self.turn_controller = TurnController(
            game_state=self.game_state,
            rules=self.rules,
            board=self.board
        )
        
        # Initialize UI components
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.main_menu = MainMenu()
        self.pause_menu = PauseMenu()
        
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
        payload = self.main_menu.show(self.screen, self.clock, has_save=has_save)
        
        if not payload:
            return

        action = payload.get("action")
        
        if action == "new_game":
            mode = payload.get("mode", "2p")
            difficulty = payload.get("difficulty")
            self._start_new_game(mode, difficulty)
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

    def _run_game(self):
        """
        Main game loop following the Input → Update → Render pattern.
        """
        # Check if AI should move first (if AI is white)
        if self.turn_controller._is_ai_turn():
            self.turn_controller._trigger_ai()
        
        while self.running and self.app_state == "playing":
            # Input: Process all events
            self._handle_events()
            
            # Check for pending AI moves and execute them
            self._check_and_execute_ai_move()
            
            # Update: Sync timer values from turn_controller to game_state
            self._update_timers()
            
            # Render: Draw the current game state
            self._render()
            
            # Control frame rate
            self.clock.tick(FPS)
    
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
            
            # Don't process moves if game is over
            if self.game_state.is_game_over:
                continue
            
            # Mouse events (handled by InputHandler)
            action = self.input_handler.handle_event(event, self.game_state)
            
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
    
    def _attempt_move(self, start_pos, end_pos):
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
        # Check the last move to determine sound to play
        last_move_index = len(self.game_state.move_log)
        
        # Ask the core to process the move
        move_successful = self.game_state.process_move(start_pos, end_pos)
        
        if move_successful:
            # Play appropriate sound based on move type
            if last_move_index < len(self.game_state.move_log):
                last_move = self.game_state.move_log[-1]
                self._play_move_sound(last_move)
            
            # Update position history BEFORE switching turns for threefold repetition
            self.rules.update_position_history(self.board)
            
            # Complete the turn (switches player)
            turn_result = self.turn_controller.complete_turn(move_successful=True)
            
            # Check game status
            if turn_result['game_over']:
                self._handle_game_over(turn_result['game_status'])
            
            # Check if it's AI's turn (for future AI implementation)
            if turn_result.get('ai_turn', False):
                self._trigger_ai_move()
        else:
            # Play illegal move sound
            self.sound_manager.play_illegal_move()
    
    def _handle_game_over(self, game_status):
        """
        Handle game over scenarios.
        
        Args:
            game_status: Dict containing status info (checkmate, stalemate, draw, etc.)
        """
        status_type = game_status.get('status', 'unknown')
        message = game_status.get('message', 'Game over')
        
        # Play game end sound
        self.sound_manager.play_game_end()
        
        # Log game over for debugging
        print(f"Game Over: {message} (Status: {status_type})")
        
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
        Update game_state timer values from turn_controller.
        
        This syncs the dynamic timer values so the renderer can display them.
        """
        if self.turn_controller.clock_enabled:
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
        self.renderer.draw(self.screen, self.game_state, self.input_handler)
        
        # Update display
        pygame.display.flip()

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
        self.running = False
        self.app_state = "quit"

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
        from agents import RandomAgent, MinimaxAgent
        
        agent_map = {
            "RandomAgent": lambda: RandomAgent("Easy Bot"),
            "MinimaxAgent": lambda: MinimaxAgent(name="Minimax Bot", depth=3),
        }
        
        factory = agent_map.get(ai_agent_type)
        if factory:
            agent = factory()
            self.enable_ai(ai_color=ai_color, ai_agent=agent)
            
            # Check if it's AI's turn after restore
            if self.turn_controller._is_ai_turn():
                self.turn_controller._trigger_ai()

    # ==================== Game Setup ====================
    
    def _start_new_game(self, mode=None, difficulty=None):
        """Start a fresh new game."""
        
        # If explicitly passed from menu, update the controller's AI settings
        if mode == "1p" and difficulty:
            from agents import RandomAgent, MinimaxAgent
            self.ai_color = 'black' # Default AI to black
            if difficulty == "easy":
                self.ai_agent = RandomAgent("Easy Bot")
            elif difficulty == "medium":
                self.ai_agent = MinimaxAgent(name="Medium Bot", depth=2)
            elif difficulty == "hard":
                self.ai_agent = MinimaxAgent(name="Hard Bot", depth=3)
        elif mode == "2p":
            # Clear AI for local multiplayer
            self.ai_agent = None
            self.ai_color = None

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
        self.turn_controller = TurnController(
            game_state=self.game_state,
            rules=self.rules,
            board=self.board
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
