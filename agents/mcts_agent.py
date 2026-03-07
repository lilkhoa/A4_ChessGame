"""
    We may use Optimized MCTS Agent because we are using Pygame to run the game, not using C/C++, if we randomly simulate to the end of the game, it will wait a very long time for the MCTS response:
        - Max Rollout Depth: MCTS just should simulate at the range 30-40 moves, then apply the material evaluation to guess who gets the benefit.
        - Heuristic Rollout: Instead of moving 100% randomly, MCTS will prioritize for "eacting" as much as possible of the pieces. Help AI does not blind of some basic strategy/
"""

import math
import random
import time

from config import EXPLORATION_CONST
from .base_agent import BaseAgent
from core.board import Board
from core.game_state import GameState
from core.move import Move



class MCTSNode:
    def __init__(self, move: Move=None, parent=None, current_turn=None):
        self.move = move
        self.parent = parent
        self.current_turn = current_turn    # Black/White side will take the next move at this node

        self.visits = 0
        self.wins = 0.0     # Calculate as the the root_color (our AI)
        self.children = {}
        self.untried_moves = []
        self.is_expanded = False
        self.is_terminal = False
    
    def ucb1(self, root_color, exploration_constant=EXPLORATION_CONST):
        """
            Compute the value of UCB1 to balance between Exploration and Exploitation
        """
        if self.visits == 0:
            return float('inf')
        
        win_rate = self.wins/self.visits

        # If this node is the opposite side makes the move (parrent.current_turn != root_color)
        # the opposite wants to choose the node that reduce our win rate
        # So, fromt the view of the opposite, we have to reverse the win rate
        if self.parent and self.parent.current_turn != root_color:
            win_rate = 1.0 - win_rate
        
        exploration = exploration_constant * math.sqrt(math.log(self.parent.visits)/ self.visits)

        return win_rate + exploration

class MCTSAgent(BaseAgent):
    """
        Monte Carlo Tree Search Agent for Chess
        Support limit the thinking time and limit the depth of the simulation progress to optimize the speed of making a move
    """
    def __init__(self, name="MCTS Bot", think_time=3.0, max_rollout_depth=30):
        super().__init__(name)
        self.think_time = think_time
        self.max_rollout_depth = max_rollout_depth

    def get_move(self, board:Board, game_state:GameState, color:str) -> Move:
        legal_moves = self.get_legal_moves(board, game_state, color)

        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]   # only one move can be made => No other choices => return immediately
        
        root = MCTSNode(current_turn=color)     # have no parrent, the current move is None either
        root.untried_moves = legal_moves.copy()

        start_time = time.time()
        iterations = 0

        # Iterate MCTS until run out of thinking time
        while time.time() - start_time <= self.think_time:
            # Selection & Expansion
            node, sim_board, sim_state = self._select_and_expand(root, board, game_state, color)

            # Simulation / Rollout
            reward = self._rollout(sim_board, sim_state, color)

            # backprop
            self._backpropagation(node, reward)

            iterations += 1

        print(f"AI {self.name} has run {iterations} iterations MCTS in {self.think_time}s.")

        # Choose the best move based on the number of visit (Robust Child)
        best_child_id = max(root.children.items(), key=lambda item: item[1].visits)[0]

        for move in legal_moves:
            if move.move_id == best_child_id:
                return move
            
        return random.choice(legal_moves)
    
    # ========================================================
    # The core steps of MCTS
    # ========================================================
    def _select_and_expand(self, root: MCTSNode, board:Board, game_state:GameState, root_color: str):
        node = root
        sim_board, sim_state = self._copy_game(board, game_state)

        # Go down the tree until the have not expansion node or game over
        while node.is_expanded and not node.is_terminal:
            # Find the node with the highest UCB1 score:
            best_move_id, best_node = max(
                node.children.items(),
                key=lambda item: item[1].ucb1(root_color)
            )

            # Execute the move in the copied board
            sim_board, sim_state = self._simulate_move(sim_board, sim_state, best_node.move, node.current_turn)
            node = best_node

        # If not terminal and there are steps that have not been tried yet
        if not node.is_terminal and node.untried_moves:
            move_to_try = random.choice(node.untried_moves)
            node.untried_moves.remove(move_to_try)

            # If this is the final legal move => Mark it as the complete expansion node, then to traverse to get the best node
            if len(node.untried_moves) == 0:
                node.is_expanded = True

            # Execute the new move
            sim_board, sim_state = self._simulate_move(sim_board, sim_state, move_to_try, node.current_turn)

            # Create child node
            next_turn = "black" if node.current_turn == "white" else "white"
            child_node = MCTSNode(move=move_to_try, parent=node, current_turn=next_turn)

            # Get the legal move for new node
            child_legal_moves = self.get_legal_moves(board=sim_board, game_state=sim_state, color=next_turn)
            child_node.untried_moves = child_legal_moves
            
            if not child_legal_moves:
                child_node.is_terminal = True
                child_node.is_expanded = True

            node.children[move_to_try.move_id] = child_node
            node = child_node

        return node, sim_board, sim_state
    
    def _rollout(self, board: Board, game_state: GameState, root_color: str) -> float:
        """
            Randomly simulate the chess board from the current state.
            Return 1.0 if root_color win, 0.0 if lose, 0.5 if draw.
        """
        current_color = game_state.current_turn
        depth = 0

        while depth < self.max_rollout_depth:
            # Check is Game Over
            if self.rules.is_checkmate(board, game_state, current_color):
                return 0.0 if current_color == root_color else 1.0
            
            if self.rules.is_stalemate(board, game_state, current_color) or self.rules.is_draw(board, game_state, current_color):
                return 0.5
            
            legal_moves = self.get_legal_moves(board, game_state, current_color)
            if not legal_moves:
                break

            # Heuristic: Prioritize capture pieces instead of randomly moving
            captures = [m for m in legal_moves if m.piece_captured is not None]
            if captures:
                chosen_move = random.choice(captures)
            else:
                chosen_move = random.choice(legal_moves)

            board, game_state = self._simulate_move(board, game_state, chosen_move, current_color)

            current_color = "black" if current_color == "white" else "white"
            depth += 1

        # If reach the depth limit, use the material eval to predict the result
        return self._evaluate_material(board, root_color)
    
    def _backpropagation(self, node: MCTSNode, reward:float):
        """
            back prop the rawrd from Terminal Node to the root
        """
        while node is not None:
            node.visits += 1
            node.wins += reward
            node = node.parent
            
    # ========================================================
    # Utilities
    # ========================================================
    def _evaluate_material(self, board: Board, root_color: str) -> float:
        """
            Evaluate if Rollout is interrupted. Return [0.0, 1.0]
        """
        values = {'pawn': 1, 'knight': 2, 'bishop': 3, 'rook': 5, 'queen': 9}

        root_score = 0
        opp_score = 0

        for r in range(8):
            for c in range(8):
                p = board.get_piece(r, c)
                if p and p.name in values:
                    if p.color == root_color:
                        root_score += values[p.name]
                    else: 
                        opp_score += values[p.name]

        total = root_score + opp_score
        if total == 0:
            return 0.5
        
        # Return rate (Sigmoid-like) to map score into range 0.0 -> 1.0
        win_prob = root_score / total
        return win_prob
    
    def _simulate_move(self, board: Board, game_state: GameState, move: Move, color: str) -> tuple:
        """
            Copy logic from MinimaxAgent to simulate safty move
        """
        new_board, new_state = self._copy_game(board, game_state)
        new_board.move_piece(move)

        is_capture = move.piece_captured is not None or getattr(move, 'is_en_passant', False)
        is_pawn_move = move.piece_moved and move.piece_moved.name == 'pawn'
        if is_pawn_move or is_capture:
            new_state.halfmove_clock = 0
        else:
            new_state.halfmove_clock += 1

        new_state.current_turn = "black" if color=="white" else "white"

        return new_board, new_state
    
    def _copy_game(self, board: Board, game_state: GameState) -> tuple:
        """
            Create deep copy of board and game_state
        """
        new_board = Board()
        new_board.grid = [[None for _ in range(8)] for _ in range(8)]

        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    piece_class = type(piece)
                    new_piece = piece_class(piece.color)
                    new_piece.has_moved = piece.has_moved
                    new_board.grid[row][col] = new_piece

        new_state = GameState(new_board, rules=game_state.rules)
        new_state.current_turn = game_state.current_turn
        new_state.halfmove_clock = game_state.halfmove_clock
        new_state.move_log = list(game_state.move_log)

        return new_board, new_state 