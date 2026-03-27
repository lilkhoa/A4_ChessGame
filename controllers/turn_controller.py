from typing import Optional, Callable
import time
import threading

class TurnController:
    """
    Controls the turn-based flow of the chess game.
    """
    
    def __init__(self, game_state, rules, board, timer=None):
        """
        Initialize the turn controller.
        
        Args:
            game_state: The game state object
            rules: The rules engine
            board: The board object
            timer: Optional Timer object for clock management
        """
        self.game_state = game_state
        self.rules = rules
        self.board = board
        self.timer = timer
        
        # Player tracking
        self.current_player = 'white'
        
        # Clock management (legacy - for backwards compatibility)
        self.white_time_remaining = 600.0
        self.black_time_remaining = 600.0
        self.white_clock_start = None
        self.black_clock_start = None
        self.clock_enabled = False
        
        # AI configuration
        self.ai_enabled = False
        self.ai_color = None
        self.ai_callback = None
        
        # Game state flags
        self.game_over = False
        self.game_over_reason = None
        self.winner = None
        
        # Move history
        self.move_count = 0
        self.turn_number = 1
        
    # ==================== Player Tracking ====================
    
    def get_current_player(self) -> str:
        """
        Get the current player.
        
        Returns:
            str: 'white' or 'black'
        """
        return self.current_player
    
    def is_player_turn(self, color: str) -> bool:
        """
        Check if it's a specific player's turn.
        
        Args:
            color: The color to check ('white' or 'black')
            
        Returns:
            bool: True if it's that player's turn
        """
        return self.current_player == color
    
    # ==================== Turn Flow ====================
    
    def process_move(self, move) -> dict:
        """
        Process a move and handle turn switching.
        
        This is the main entry point for executing a move. It:
        1. Validates the move belongs to the current player
        2. Executes the move (delegated to game_controller or board)
        3. Switches turns
        4. Checks for game over conditions
        5. Triggers AI if needed
        
        Args:
            move: The move to process
            
        Returns:
            dict: Result containing success status and any messages
        """
        if self.game_over:
            return {
                'success': False,
                'message': f'Game is over: {self.game_over_reason}',
                'game_over': True
            }
        
        # Validate it's the correct player's turn
        piece = self.board.get_piece(move.start_row, move.start_col)
        if piece is None:
            return {
                'success': False,
                'message': 'No piece at starting position'
            }
        
        if piece.color != self.current_player:
            return {
                'success': False,
                'message': f"It's {self.current_player}'s turn"
            }
        
        return {
            'success': True,
            'message': 'Move validated, ready for execution',
            'current_player': self.current_player
        }
    
    def complete_turn(self, move_successful: bool = True) -> dict:
        """
        Complete the current turn and switch to the next player.
        
        This should be called by game_controller AFTER a move is executed.
        It handles:
        1. Stopping current player's clock
        2. Switching to the next player
        3. Starting next player's clock
        4. Checking for game over conditions
        5. Triggering AI if applicable
        
        Args:
            move_successful: Whether the move was successfully executed
            
        Returns:
            dict: Information about the turn completion and game state
        """
        if not move_successful:
            return {
                'success': False,
                'message': 'Move was not successful, turn not completed'
            }
        
        # Stop current player's clock
        self._stop_clock(self.current_player)
        
        # Switch to next player
        self._switch_player()
        
        # Start next player's clock
        self._start_clock(self.current_player)
        
        # Update turn counter
        if self.current_player == 'white':
            self.turn_number += 1
        
        # Check for game over conditions
        game_status = self._check_game_over()
        
        result = {
            'success': True,
            'current_player': self.current_player,
            'turn_number': self.turn_number,
            'game_over': self.game_over,
            'game_status': game_status
        }
        
        # If game is not over and it's AI's turn, trigger AI
        if not self.game_over and self._is_ai_turn():
            result['ai_turn'] = True
            self._trigger_ai()
        
        return result
    
    def _switch_player(self):
        """Switch to the other player."""
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        self.move_count += 1
        
        # Switch timer to the new current player
        if self.timer:
            self.timer.switch_turn()
        
        # Update game state if it exists
        if hasattr(self.game_state, 'current_turn'):
            self.game_state.current_turn = self.current_player
    
    # ==================== Game Over Detection ====================
    
    def _check_game_over(self) -> dict:
        """
        Check if the game is over after a turn switch.
        
        Checks for (in order):
        - Time out (if timer is enabled)
        - Checkmate
        - Stalemate
        - Draw (threefold repetition, fifty-move rule, insufficient material)
        
        Returns:
            dict: Game status information
        """
        # Check for timeout first (server-side timeout takes precedence)
        if self.timer and self.timer.is_timeout():
            self.game_over = True
            timed_out_color = self.timer.is_timeout()
            self.winner = 'black' if timed_out_color == 'white' else 'white'
            self.game_over_reason = 'timeout'
            self.game_state.timeout_winner = self.winner
            return {
                'status': 'timeout',
                'timed_out_player': timed_out_color,
                'winner': self.winner,
                'message': f'{timed_out_color.capitalize()} ran out of time. {self.winner.capitalize()} wins!'
            }
        
        current_color = self.current_player
        
        # Update game_state's game over flags
        self.game_state.check_game_over()
        
        # Check for checkmate
        if self.rules.is_checkmate(self.board, self.game_state, current_color):
            self.game_over = True
            self.game_over_reason = 'checkmate'
            self.winner = 'black' if current_color == 'white' else 'white'
            return {
                'status': 'checkmate',
                'winner': self.winner,
                'message': f'{self.winner.capitalize()} wins by checkmate!'
            }
        
        # Check for draw conditions
        if self.rules.is_draw(self.board, self.game_state, current_color):
            self.game_over = True
            self.winner = None
            
            # Determine specific draw reason and update game_state
            if self.rules.is_insufficient_material(self.board):
                self.game_over_reason = 'insufficient_material'
                self.game_state.draw_reason = 'insufficient_material'
                message = 'Game drawn by insufficient material'
            elif self.rules.is_threefold_repetition(self.board):
                self.game_over_reason = 'threefold_repetition'
                self.game_state.draw_reason = 'threefold_repetition'
                message = 'Game drawn by threefold repetition'
            elif self.rules.is_fifty_move_rule(self.game_state):
                self.game_over_reason = 'fifty_move_rule'
                self.game_state.draw_reason = 'fifty_move_rule'
                message = 'Game drawn by fifty-move rule'
            elif self.rules.is_stalemate(self.board, self.game_state, current_color):
                self.game_over_reason = 'stalemate'
                self.game_state.draw_reason = 'stalemate'
                message = 'Game drawn by stalemate'
            else:
                self.game_over_reason = 'draw'
                self.game_state.draw_reason = 'draw'
                message = 'Game drawn'
            
            return {
                'status': self.game_over_reason,
                'winner': None,
                'message': message
            }
        
        if self.rules.is_in_check(self.board, current_color):
            return {
                'status': 'check',
                'in_check': True,
                'message': f'{current_color.capitalize()} is in check!'
            }
        
        # Game continues normally
        return {
            'status': 'ongoing',
            'message': f"{current_color.capitalize()}'s turn"
        }
    
    def is_game_over(self) -> bool:
        """
        Check if the game is over.
        
        Returns:
            bool: True if the game is over
        """
        return self.game_over
    
    def get_game_result(self) -> dict:
        """
        Get the game result.
        
        Returns:
            dict: Game result information
        """
        return {
            'game_over': self.game_over,
            'reason': self.game_over_reason,
            'winner': self.winner
        }
    
    # ==================== Clock Management ====================
    
    def enable_clock(self, time_per_player: float = 300.0):
        """
        Enable the game clock.
        
        Args:
            time_per_player: Time in seconds for each player (default: 300 = 5 minutes)
        """
        self.clock_enabled = True
        self.white_time_remaining = time_per_player
        self.black_time_remaining = time_per_player
        
        self._start_clock(self.current_player)
    
    def disable_clock(self):
        """Disable the game clock."""
        self._stop_clock(self.current_player)
        self.clock_enabled = False
        self.white_clock_start = None
        self.black_clock_start = None
    
    def _start_clock(self, color: str):
        """
        Start the clock for a specific player.
        
        Args:
            color: The color whose clock to start
        """
        if not self.clock_enabled:
            return
        
        current_time = time.time()
        
        if color == 'white':
            self.white_clock_start = current_time
        else:
            self.black_clock_start = current_time
    
    def _stop_clock(self, color: str):
        """
        Stop the clock for a specific player and update their remaining time.
        
        Args:
            color: The color whose clock to stop
        """
        if not self.clock_enabled:
            return
        
        current_time = time.time()
        
        if color == 'white' and self.white_clock_start is not None:
            elapsed = current_time - self.white_clock_start
            self.white_time_remaining -= elapsed
            self.white_clock_start = None
            
            # Check if time ran out
            if self.white_time_remaining <= 0:
                self._handle_timeout('white')
                
        elif color == 'black' and self.black_clock_start is not None:
            elapsed = current_time - self.black_clock_start
            self.black_time_remaining -= elapsed
            self.black_clock_start = None
            
            # Check if time ran out
            if self.black_time_remaining <= 0:
                self._handle_timeout('black')
    
    def get_time_remaining(self, color: str) -> float:
        """
        Get the remaining time for a player.
        
        Args:
            color: The color to check
            
        Returns:
            float: Time remaining in seconds
        """
        # If timer exists, use it (new system)
        if self.timer:
            return self.timer.get_remaining_time(color)
        
        # Otherwise use legacy clock system
        if not self.clock_enabled:
            return float('inf')
        
        # Update the time if clock is currently running
        if color == self.current_player:
            if color == 'white' and self.white_clock_start is not None:
                elapsed = time.time() - self.white_clock_start
                return max(0, self.white_time_remaining - elapsed)
            elif color == 'black' and self.black_clock_start is not None:
                elapsed = time.time() - self.black_clock_start
                return max(0, self.black_time_remaining - elapsed)
        
        return self.white_time_remaining if color == 'white' else self.black_time_remaining
    
    def _handle_timeout(self, color: str):
        """
        Handle a player running out of time.
        
        Args:
            color: The color that ran out of time
        """
        self.game_over = True
        self.game_over_reason = 'timeout'
        self.winner = 'black' if color == 'white' else 'white'
    
    # ==================== AI Integration ====================
    
    def enable_ai(self, ai_color: str, ai_callback: Callable):
        """
        Enable AI for a specific color.
        
        Args:
            ai_color: The color the AI will play ('white' or 'black')
            ai_callback: Function to call when it's AI's turn
                        Should have signature: callback(board, game_state, color) -> move
        """
        self.ai_enabled = True
        self.ai_color = ai_color
        self.ai_callback = ai_callback
    
    def disable_ai(self):
        """Disable AI."""
        self.ai_enabled = False
        self.ai_color = None
        self.ai_callback = None
    
    def _is_ai_turn(self) -> bool:
        """
        Check if it's the AI's turn.
        
        Returns:
            bool: True if AI should move now
        """
        return self.ai_enabled and self.current_player == self.ai_color
    
    def _trigger_ai(self):
        """
        Trigger the AI to make a move.
        
        This will call the AI callback function (e.g., Minimax, Alpha-Beta pruning)
        in a background thread to prevent UI freezing. The callback should return 
        a move, which will then be processed in the main thread next frame.
        """
        if not self._is_ai_turn() or self.ai_callback is None:
            return
        
        def ai_worker():
            try:
                # Call the AI algorithm to get the best move
                ai_move = self.ai_callback(self.board, self.game_state, self.ai_color)
                
                # Store the move for game controller to execute
                self.game_state.pending_ai_move = ai_move
                    
            except Exception as e:
                print(f"AI error: {e}")
                import traceback
                traceback.print_exc()
                # If AI fails, human can take over
                
        # Run AI calculation in background so UI remains responsive
        ai_thread = threading.Thread(target=ai_worker)
        ai_thread.daemon = True
        ai_thread.start()
    
    # ==================== Utility Methods ====================
    
    def reset(self):
        """Reset the turn controller for a new game."""
        self.current_player = 'white'
        self.game_over = False
        self.game_over_reason = None
        self.winner = None
        self.move_count = 0
        self.turn_number = 1
        
        # Reset clocks
        if self.clock_enabled:
            self._stop_clock('white')
            self._stop_clock('black')
            time_per_player = max(self.white_time_remaining, self.black_time_remaining)
            self.enable_clock(time_per_player)
        
        # Reset rules history
        self.rules.reset_position_history()
    
    def get_turn_info(self) -> dict:
        """
        Get current turn information.
        
        Returns:
            dict: Complete turn information
        """
        return {
            'current_player': self.current_player,
            'turn_number': self.turn_number,
            'move_count': self.move_count,
            'game_over': self.game_over,
            'game_over_reason': self.game_over_reason,
            'winner': self.winner,
            'white_time': self.get_time_remaining('white') if self.clock_enabled else None,
            'black_time': self.get_time_remaining('black') if self.clock_enabled else None,
            'ai_enabled': self.ai_enabled,
            'ai_color': self.ai_color,
            'is_ai_turn': self._is_ai_turn()
        }
