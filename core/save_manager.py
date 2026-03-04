# core/save_manager.py

import json
import os

from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King

# Mapping from piece name to class for deserialization
PIECE_CLASS_MAP = {
    "pawn": Pawn,
    "rook": Rook,
    "knight": Knight,
    "bishop": Bishop,
    "queen": Queen,
    "king": King,
}

# Default save directory and file
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")


class SaveManager:
    """
    Handles saving and loading chess game state to/from a JSON file.
    """

    @staticmethod
    def _serialize_piece(piece):
        """Convert a piece object to a JSON-friendly dict."""
        if piece is None:
            return None
        return {
            "name": piece.name,
            "color": piece.color,
            "has_moved": piece.has_moved,
        }

    @staticmethod
    def _deserialize_piece(data):
        """Reconstruct a piece object from a dict."""
        if data is None:
            return None
        cls = PIECE_CLASS_MAP.get(data["name"])
        if cls is None:
            return None
        piece = cls(data["color"])
        piece.has_moved = data["has_moved"]
        return piece

    @staticmethod
    def _serialize_board(board_grid):
        """Serialize the 8x8 board grid."""
        return [
            [SaveManager._serialize_piece(board_grid[r][c]) for c in range(8)]
            for r in range(8)
        ]

    @staticmethod
    def _deserialize_board(board_data):
        """Deserialize the 8x8 board grid."""
        return [
            [SaveManager._deserialize_piece(board_data[r][c]) for c in range(8)]
            for r in range(8)
        ]

    @staticmethod
    def _serialize_move_log(move_log):
        """Serialize move log entries."""
        serialized = []
        for entry in move_log:
            piece = entry["piece"]
            captured = entry.get("captured")
            serialized.append({
                "piece": SaveManager._serialize_piece(piece) if hasattr(piece, 'name') else None,
                "start": list(entry["start"]),
                "end": list(entry["end"]),
                "captured": SaveManager._serialize_piece(captured) if hasattr(captured, 'name') else None,
            })
        return serialized

    @staticmethod
    def _deserialize_move_log(move_log_data):
        """Deserialize move log entries, reconstructing Piece objects."""
        deserialized = []
        for entry in move_log_data:
            deserialized.append({
                "piece": SaveManager._deserialize_piece(entry["piece"]),
                "start": tuple(entry["start"]),
                "end": tuple(entry["end"]),
                "captured": SaveManager._deserialize_piece(entry.get("captured")),
            })
        return deserialized

    @staticmethod
    def save_game(game_controller):
        """
        Save the current game state to a JSON file.

        Args:
            game_controller: The GameController instance

        Returns:
            bool: True if save was successful
        """
        try:
            gs = game_controller.game_state
            tc = game_controller.turn_controller

            state = {
                # Board
                "board": SaveManager._serialize_board(gs.board),

                # Turn info
                "current_turn": gs.current_turn,
                "halfmove_clock": gs.halfmove_clock,

                # Move log
                "move_log": SaveManager._serialize_move_log(gs.move_log),

                # Game over flags
                "is_checkmate": gs.is_checkmate,
                "is_draw": gs.is_draw,
                "draw_reason": gs.draw_reason,
                "timeout_winner": gs.timeout_winner,

                # Clock
                "clock_enabled": game_controller.clock_enabled,
                "time_per_player": game_controller.time_per_player,
                "white_time": tc.get_time_remaining('white') if tc.clock_enabled else 300.0,
                "black_time": tc.get_time_remaining('black') if tc.clock_enabled else 300.0,

                # AI config (save type, not the agent object)
                "ai_color": game_controller.ai_color,
                "ai_agent_name": game_controller.ai_agent.name if game_controller.ai_agent else None,
                "ai_agent_type": type(game_controller.ai_agent).__name__ if game_controller.ai_agent else None,

                # Turn controller state
                "turn_number": tc.turn_number,
                "move_count": tc.move_count,
                "game_over": tc.game_over,
                "game_over_reason": tc.game_over_reason,
                "winner": tc.winner,
            }

            # Ensure save directory exists
            os.makedirs(SAVE_DIR, exist_ok=True)

            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            print(f"Game saved to {SAVE_FILE}")
            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def load_game():
        """
        Load a saved game state from the JSON file.

        Returns:
            dict or None: The saved state dict, or None if no save exists
        """
        if not SaveManager.has_save():
            return None

        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state
        except Exception as e:
            print(f"Error loading save: {e}")
            return None

    @staticmethod
    def has_save():
        """
        Check if a valid save file exists.

        Returns:
            bool: True if a save file exists and is readable
        """
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Basic validation
            return "board" in data and "current_turn" in data
        except Exception:
            return False

    @staticmethod
    def delete_save():
        """Remove the save file (e.g., after game over)."""
        try:
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
                print("Save file deleted.")
        except Exception as e:
            print(f"Error deleting save: {e}")

    @staticmethod
    def restore_game_state(game_controller, state):
        """
        Restore a GameController from a saved state dict.

        Args:
            game_controller: The GameController instance to restore into
            state: The saved state dict from load_game()
        """
        from core.board import Board
        from core.game_state import GameState
        from core.rules import Rules
        from controllers.turn_controller import TurnController

        # Rebuild board
        board = Board()
        board.grid = SaveManager._deserialize_board(state["board"])

        # Rebuild rules and game state
        rules = Rules()
        game_state = GameState(board, rules=rules)
        game_state.current_turn = state["current_turn"]
        game_state.halfmove_clock = state.get("halfmove_clock", 0)
        game_state.is_checkmate = state.get("is_checkmate", False)
        game_state.is_draw = state.get("is_draw", False)
        game_state.draw_reason = state.get("draw_reason", None)
        game_state.timeout_winner = state.get("timeout_winner", None)

        # Rebuild move log with proper Piece objects for en passant etc.
        game_state.move_log = SaveManager._deserialize_move_log(state.get("move_log", []))

        # Rebuild turn controller
        turn_controller = TurnController(
            game_state=game_state,
            rules=rules,
            board=board
        )
        turn_controller.current_player = state["current_turn"]
        turn_controller.turn_number = state.get("turn_number", 1)
        turn_controller.move_count = state.get("move_count", 0)
        turn_controller.game_over = state.get("game_over", False)
        turn_controller.game_over_reason = state.get("game_over_reason", None)
        turn_controller.winner = state.get("winner", None)

        # Apply to game controller
        game_controller.board = board
        game_controller.rules = rules
        game_controller.game_state = game_state
        game_controller.turn_controller = turn_controller

        # Restore clock
        clock_enabled = state.get("clock_enabled", False)
        if clock_enabled:
            game_controller.clock_enabled = True
            game_controller.time_per_player = state.get("time_per_player", 300.0)
            turn_controller.clock_enabled = True
            turn_controller.white_time_remaining = state.get("white_time", 300.0)
            turn_controller.black_time_remaining = state.get("black_time", 300.0)
            # Start clock for current player
            turn_controller._start_clock(turn_controller.current_player)

        # Restore timer display values
        game_state.white_time = state.get("white_time", 300.0)
        game_state.black_time = state.get("black_time", 300.0)

        # Restore AI
        ai_agent_type = state.get("ai_agent_type")
        ai_color = state.get("ai_color")
        if ai_agent_type and ai_color:
            game_controller._restore_ai(ai_agent_type, ai_color)
            # Update input handler's reversed view if AI is white (player is black)
            game_controller.input_handler.reversed_view = (ai_color == 'white')
        else:
            game_controller.input_handler.reversed_view = False

        # Clear input handler
        game_controller.input_handler.reset()

        print("Game restored from save.")
