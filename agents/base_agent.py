from abc import ABC, abstractmethod
from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from core.move import Move


class BaseAgent(ABC):
    """
    Abstract base class for all chess agents.
    """
    
    def __init__(self, name: str = "BaseAgent"):
        """
        Initialize the base agent.
        
        Args:
            name (str): The name of the agent for display purposes
        """
        self.name = name
        self.moves_made = 0
        self.game_history = []
        self.rules = Rules()
    
    @abstractmethod
    def get_move(self, board: Board, game_state: GameState, color: str) -> Move:
        """
        Get the next move for the given board position.
        
        This is the main method that each agent must implement.
        It should analyze the current board position and return the best move
        according to the agent's algorithm.
        
        Args:
            board (Board): The current chess board object
            game_state (GameState): The current game state
            color (str): The color this agent is playing ('white' or 'black')
            
        Returns:
            Move: The move the agent wants to make, or None if no legal moves
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    def make_move(self, board: Board, game_state: GameState, color: str) -> Move:
        """
        Make a move on the board and track it.
        
        This method calls get_move() to determine the move, then applies it
        to the board and updates the agent's internal tracking.
        
        Args:
            board (Board): The current chess board object
            game_state (GameState): The current game state
            color (str): The color this agent is playing ('white' or 'black')
            
        Returns:
            Move: The move that was made, or None if no legal moves
        """
        # Check if game is already over
        if game_state.is_game_over:
            return None
            
        move = self.get_move(board, game_state, color)
        if move is None:
            return None
        
        legal_moves = self.rules.get_all_legal_moves(board, game_state, color)
        
        is_legal = False
        for legal_move in legal_moves:
            if (move.start_row == legal_move.start_row and 
                move.start_col == legal_move.start_col and
                move.end_row == legal_move.end_row and 
                move.end_col == legal_move.end_col):
                is_legal = True
                break
        
        if is_legal:
            success = game_state.process_move(
                (move.start_row, move.start_col),
                (move.end_row, move.end_col)
            )
            
            if success:
                self.moves_made += 1
                self.game_history.append(move)
                return move
                
        return None
    
    def reset(self):
        """Reset the agent's state for a new game."""
        self.moves_made = 0
        self.game_history = []
    
    def get_legal_moves(self, board: Board, game_state: GameState, color: str) -> list:
        """
        Get all legal moves for the given position.
        
        This is a convenience method that agents can use to get legal moves.
        
        Args:
            board (Board): The current chess board object
            game_state (GameState): The current game state
            color (str): The color to get legal moves for
            
        Returns:
            list: List of legal Move objects
        """
        return self.rules.get_all_legal_moves(board, game_state, color)
    
    def get_stats(self) -> dict:
        """
        Get statistics about the agent's performance.
        
        Returns:
            dict: Dictionary containing agent statistics
        """
        return {
            'name': self.name,
            'moves_made': self.moves_made,
            'game_history_length': len(self.game_history)
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} (Moves: {self.moves_made})"
    
    def __repr__(self) -> str:
        """Developer representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', moves_made={self.moves_made})"
