import pygame
import time
from config import SQUARE_SIZE, ANIMATION_DURATION, BOARD_OFFSET_X, BOARD_OFFSET_Y


class Animation:
    """Handles move animations and visual effects for the chess game."""

    def __init__(self):
        self.animating = False
        self.current_animation = None

    def animate_move(self, screen, board_ui, piece_ui, piece, start_sq, end_sq,
                     board_grid, game_state, clock, draw_callback=None, reversed_view=False):
        """
        Animate a piece moving from start_sq to end_sq with smooth interpolation.

        Args:
            screen: Pygame display surface
            board_ui: BoardUI instance
            piece_ui: PieceUI instance
            piece: The Piece object being moved
            start_sq: (row, col) start position
            end_sq: (row, col) end position
            board_grid: The board grid (piece has already been moved in logic)
            game_state: Current game state
            clock: Pygame clock for frame timing
            draw_callback: Optional function to draw additional elements during animation
        """
        self.animating = True

        sr, sc = start_sq
        er, ec = end_sq

        display_sc = (7 - sc) if reversed_view else sc
        display_sr = (7 - sr) if reversed_view else sr
        display_ec = (7 - ec) if reversed_view else ec
        display_er = (7 - er) if reversed_view else er

        start_x = BOARD_OFFSET_X + display_sc * SQUARE_SIZE + SQUARE_SIZE // 2
        start_y = BOARD_OFFSET_Y + display_sr * SQUARE_SIZE + SQUARE_SIZE // 2
        end_x = BOARD_OFFSET_X + display_ec * SQUARE_SIZE + SQUARE_SIZE // 2
        end_y = BOARD_OFFSET_Y + display_er * SQUARE_SIZE + SQUARE_SIZE // 2

        duration = ANIMATION_DURATION
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            t = min(elapsed / duration, 1.0)

            # Ease-out cubic for smooth deceleration
            t_eased = 1.0 - (1.0 - t) ** 3

            current_x = start_x + (end_x - start_x) * t_eased
            current_y = start_y + (end_y - start_y) * t_eased

            # Process events during animation (allow quit)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.animating = False
                    pygame.quit()
                    return

            # Redraw the scene with the piece at its interpolated position
            board_ui.draw_board(screen, reversed_view=reversed_view)

            # Draw highlights for last move
            last_move_highlight = {"start": start_sq, "end": end_sq}
            board_ui.draw_highlights(screen, last_move=last_move_highlight, reversed_view=reversed_view)

            # Draw all pieces except the one currently moving
            piece_ui.draw_pieces(screen, board_grid, skip_pos=start_sq, reversed_view=reversed_view)

            # Draw the animated piece at its interpolated position
            piece_ui.draw_piece_at(screen, piece, (current_x, current_y))

            # Draw additional elements (sidebar, etc.)
            if draw_callback:
                draw_callback()

            pygame.display.flip()
            clock.tick(60)

            if t >= 1.0:
                break

        self.animating = False

    def animate_capture_effect(self, screen, pos, clock):
        """
        Play a brief flash effect on a capture square.

        Args:
            screen: Pygame display surface
            pos: (row, col) where the capture occurred
            clock: Pygame clock
        """
        row, col = pos
        cx = BOARD_OFFSET_X + col * SQUARE_SIZE + SQUARE_SIZE // 2
        cy = BOARD_OFFSET_Y + row * SQUARE_SIZE + SQUARE_SIZE // 2

        max_radius = SQUARE_SIZE // 2
        duration = 0.12
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            t = min(elapsed / duration, 1.0)

            radius = int(max_radius * t)
            alpha = int(180 * (1.0 - t))

            effect = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                effect,
                (255, 200, 50, alpha),
                (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
                radius,
                3
            )
            x = BOARD_OFFSET_X + col * SQUARE_SIZE
            y = BOARD_OFFSET_Y + row * SQUARE_SIZE
            # The effect surface is sized SQUARE_SIZE x SQUARE_SIZE with a circle centered in it
            screen.blit(effect, (x, y))
            pygame.display.flip()
            clock.tick(60)

            if t >= 1.0:
                break

    def is_animating(self):
        """Check if an animation is currently playing."""
        return self.animating
