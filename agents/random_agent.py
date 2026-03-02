import random
from .base_agent import BaseAgent

class RandomAgent(BaseAgent):
    """
    A simple agent that selects a random legal move from the current position.
    
    This agent does not use any strategy or evaluation. It simply generates
    all legal moves and picks one at random. This can be useful for testing
    or as a baseline for more complex agents.
    """
    
    def __init__(self, name: str = "RandomAgent", seed: int = None):
        super().__init__(name)
        if seed is not None:
            random.seed(seed)
        self.seed = seed
    
    def get_move(self, board, game_state, color):
        """
        Get a random legal move for the current position.
        
        Args:
            board: The current chess board object
            game_state: The current game state
            color: The color this agent is playing ('white' or 'black')
        Returns:
            A Move object representing the chosen move, or None if no legal moves
        """
        legal_moves = self.get_legal_moves(board, game_state, color)
        
        if not legal_moves:
            return None
        
        return random.choice(legal_moves)
