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
        self.game_state = GameState(self.board)
        self.rules = Rules()
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
        
    def run(self):
        """
        Main game loop following the Input → Update → Render pattern.
        
        This loop continues until the player closes the window or quits the game.
        """
        while self.running:
            # Input: Process all events
            self._handle_events()
            
            # Update: Game state updates happen in event handlers
            # (No continuous updates needed for turn-based chess)
            
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
            # Move was successful - complete the turn
            turn_result = self.turn_controller.complete_turn(move_successful=True)
            
            # Update position history for threefold repetition detection
            self.rules.update_position_history(self.board)
            
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

    
    def _trigger_ai_move(self):
        """
        Trigger AI to make a move (placeholder for future AI integration).
        """

        # Future AI implementation will go here
        # For now, this is just a placeholder
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
        self.game_state = GameState(self.board)
        self.rules = Rules()
        self.turn_controller = TurnController(
            game_state=self.game_state,
            rules=self.rules,
            board=self.board
        )
        
        # Clear input handler state
        self.input_handler.selected_square = None
        self.input_handler.valid_moves = []
        self.input_handler.dragging = False
        self.input_handler.drag_piece = None
        self.input_handler.drag_start = None
    
    def enable_clock(self, time_per_player=600.0):
        """
        Enable the game clock with specified time control.
        
        Args:
            time_per_player: Time in seconds for each player (default: 10 minutes)
        """
        self.turn_controller.enable_clock(time_per_player)
    
    def enable_ai(self, ai_color, ai_callback):
        """
        Enable AI for a specific color.
        
        Args:
            ai_color: 'white' or 'black'
            ai_callback: Function to call for AI moves
        """
        self.turn_controller.enable_ai(ai_color, ai_callback)
    
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
