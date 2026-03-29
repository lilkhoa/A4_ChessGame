import pygame
from config import SQUARE_SIZE, BOARD_WIDTH, BOARD_HEIGHT
from ui.board_ui import BoardUI


class InputHandler:
    """
    Handles mouse input for selecting and moving chess pieces.
    Supports both click-to-select and drag-and-drop interaction.
    """

    def __init__(self):
        self.selected_square = None   # (row, col) of the selected piece
        self.valid_moves = []         # List of (row, col) valid targets
        self.dragging = False
        self.drag_piece = None        # Reference to the piece being dragged
        self.drag_start = None        # (row, col) where drag started
        self.mouse_pos = (0, 0)       # Current mouse position for drag rendering
        self.reversed_view = False    # Whether board is reversed for black player

    def handle_event(self, event, game_state, turn_controller=None, is_online_opponent_turn=False):
        """
        Process a Pygame event and return an action dict if a move is attempted.

        Args:
            event: A pygame.event.Event
            game_state: The current GameState object
            turn_controller: Optional. The current TurnController object.

        Returns:
            dict or None:
                {"type": "move", "start": (r,c), "end": (r,c)} if a move is attempted
                {"type": "deselect"} if the selection was cleared
                None if no actionable event occurred
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_mouse_down(event.pos, game_state, turn_controller, is_online_opponent_turn)

        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._handle_mouse_up(event.pos, game_state, turn_controller, is_online_opponent_turn)

        return None

    def _handle_mouse_down(self, mouse_pos, game_state, turn_controller=None, is_online_opponent_turn=False):
        """Handle left mouse button press."""
        if (turn_controller and turn_controller._is_ai_turn()) or is_online_opponent_turn:
            self._clear_selection()
            return {"type": "deselect"}
            
        clicked_sq = BoardUI.get_square_from_pos(mouse_pos, self.reversed_view)

        if clicked_sq is None:
            # Clicked outside the board
            self._clear_selection()
            return {"type": "deselect"}

        row, col = clicked_sq
        board = game_state.board
        piece = board[row][col]

        if self.selected_square is not None:
            # A piece is already selected — try to move
            if clicked_sq in self.valid_moves:
                action = {
                    "type": "move",
                    "start": self.selected_square,
                    "end": clicked_sq
                }
                self._clear_selection()
                return action

            # Clicked on own piece — re-select
            if piece and piece.color == game_state.current_turn:
                self._select_piece(clicked_sq, piece, game_state)
                return None

            # Clicked on empty/enemy square not in valid moves — deselect
            self._clear_selection()
            return {"type": "deselect"}

        else:
            # Nothing selected — select a piece if it's the current player's
            if piece and piece.color == game_state.current_turn:
                self._select_piece(clicked_sq, piece, game_state)
            return None

    def _handle_mouse_up(self, mouse_pos, game_state, turn_controller=None, is_online_opponent_turn=False):
        """Handle left mouse button release (for drag-and-drop)."""
        if (turn_controller and turn_controller._is_ai_turn()) or is_online_opponent_turn:
            self.dragging = False
            self.drag_piece = None
            return None
            
        if not self.dragging:
            return None

        release_sq = BoardUI.get_square_from_pos(mouse_pos, self.reversed_view)
        start = self.drag_start
        self.dragging = False
        self.drag_piece = None

        if release_sq is None or release_sq == start:
            # Dropped outside board or on same square — keep selection
            return None

        if release_sq in self.valid_moves:
            action = {
                "type": "move",
                "start": start,
                "end": release_sq
            }
            self._clear_selection()
            return action

        # Invalid drop target — keep selection
        return None

    def _select_piece(self, sq, piece, game_state):
        """Select a piece and calculate its valid moves."""
        self.selected_square = sq
        row, col = sq

        # Get valid moves from the piece
        last_move = game_state.move_log[-1] if game_state.move_log else None

        # Check if the piece's get_valid_moves accepts last_move (Pawn does)
        try:
            raw_moves = piece.get_valid_moves(game_state.board, row, col, last_move)
        except TypeError:
            raw_moves = piece.get_valid_moves(game_state.board, row, col)

        # Filter: only include moves that don't leave king in check
        # self.valid_moves = self._filter_legal_moves(
        #     game_state, sq, raw_moves, piece.color
        # )
        self.valid_moves = game_state.rules.get_legal_moves_for_piece(
            game_state.board_obj, piece, row, col, last_move
        )

        # Start dragging immediately
        self.dragging = True
        self.drag_piece = piece
        self.drag_start = sq

    def _filter_legal_moves(self, game_state, start_sq, moves, color):
        """
        Filter out moves that would leave the king in check.

        Args:
            game_state: Current GameState
            start_sq: (row, col) of the piece being moved
            moves: List of (row, col) candidate moves
            color: Color of the moving piece

        Returns:
            List of legal (row, col) moves
        """
        legal = []
        board = game_state.board
        sr, sc = start_sq

        for end_sq in moves:
            er, ec = end_sq

            # Simulate the move
            original_piece = board[sr][sc]
            captured_piece = board[er][ec]

            # Handle en passant capture for simulation
            en_passant_captured = None
            if original_piece.name == "pawn" and sc != ec and board[er][ec] is None:
                en_passant_captured = board[sr][ec]
                board[sr][ec] = None

            board[er][ec] = original_piece
            board[sr][sc] = None

            # Check if king is still safe
            if not self._is_king_in_check(board, color):
                legal.append(end_sq)

            # Undo simulation
            board[sr][sc] = original_piece
            board[er][ec] = captured_piece
            if en_passant_captured is not None:
                board[sr][ec] = en_passant_captured

        return legal

    def _is_king_in_check(self, board, color):
        """Check if the king of the given color is in check."""
        king_pos = None
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.name == "king" and p.color == color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break

        if king_pos is None:
            return False

        opponent = "black" if color == "white" else "white"
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.color == opponent:
                    try:
                        attacks = p.get_valid_moves(board, r, c, None)
                    except TypeError:
                        attacks = p.get_valid_moves(board, r, c)
                    if king_pos in attacks:
                        return True
        return False

    def _clear_selection(self):
        """Clear the current selection state."""
        self.selected_square = None
        self.valid_moves = []
        self.dragging = False
        self.drag_piece = None
        self.drag_start = None

    def get_king_in_check_pos(self, game_state):
        """
        Return the position of the current player's king if it's in check.

        Returns:
            (row, col) or None
        """
        color = game_state.current_turn
        board = game_state.board
        # if self._is_king_in_check(board, color):
        #     for r in range(8):
        #         for c in range(8):
        #             p = board[r][c]
        #             if p and p.name == "king" and p.color == color:
        #                 return (r, c)
        if game_state.rules.is_in_check(game_state.board_obj, color):
            for r in range(8):
                for c in range(8):
                    p = game_state.board[r][c]
                    if p and p.name == "king" and p.color == color:
                        return (r, c)
        return None

    def reset(self):
        """Reset input handler state for a new game."""
        self._clear_selection()
        self.mouse_pos = (0, 0)
