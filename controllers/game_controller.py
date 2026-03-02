import pygame
from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from controllers.turn_controller import TurnController
from ui.renderer import Renderer
from ui.input_handler import InputHandler
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, COLOR_BG


class GameController:
    """
    Main game controller that bridges the core logic and UI rendering.
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
        
        # Game state flags
        self.running = True
        
        # Clock settings for reset
        self.clock_enabled = False
        self.time_per_player = 300.0  # Default: 5 minutes
        
        # AI settings for reset
        self.ai_agent = None
        self.ai_color = None
        
    def run(self):
        """
        Main game loop following the Input → Update → Render pattern.
        
        This loop continues until the player closes the window or quits the game.
        """
        # Check if AI should move first (if AI is white)
        if self.turn_controller._is_ai_turn():
            self.turn_controller._trigger_ai()
        
        while self.running:
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
        
        # Clean up
        pygame.quit()
    
    def _handle_events(self):
        """Process all input events from the player."""
        for event in pygame.event.get():
            # Window close event
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reset game
                    self._reset_game()
            
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
        # Ask the core to process the move
        move_successful = self.game_state.process_move(start_pos, end_pos)
        
        if move_successful:
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
    
    def _handle_game_over(self, game_status):
        """
        Handle game over scenarios.
        
        Args:
            game_status: Dict containing status info (checkmate, stalemate, draw, etc.)
        """
        status_type = game_status.get('status', 'unknown')
        message = game_status.get('message', 'Game over')
        
        # Log game over for debugging
        print(f"Game Over: {message} (Status: {status_type})")

    
    def _update_timers(self):
        """
        Update game_state timer values from turn_controller.
        
        This syncs the dynamic timer values so the renderer can display them.
        """
        if self.turn_controller.clock_enabled:
            self.game_state.white_time = self.turn_controller.get_time_remaining('white')
            self.game_state.black_time = self.turn_controller.get_time_remaining('black')
            self.game_state.timeout_winner = self.turn_controller.winner if self.turn_controller.game_over_reason == 'timeout' else None
    
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
        self.input_handler.selected_square = None
        self.input_handler.valid_moves = []
        self.input_handler.dragging = False
        self.input_handler.drag_piece = None
        self.input_handler.drag_start = None
    
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
