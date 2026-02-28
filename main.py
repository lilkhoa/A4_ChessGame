"""
Chess Game - Main Entry Point
Initializes Pygame and runs the game loop.
"""
import pygame
import sys
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BOARD_WIDTH, FPS, COLOR_BG
)
from core.board import Board
from core.game_state import GameState
from ui.renderer import Renderer
from ui.input_handler import InputHandler


def main():
    pygame.init()
    pygame.display.set_caption("Chess Game")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Initialize game objects
    board_obj = Board()
    game_state = GameState(board_obj)
    renderer = Renderer()
    input_handler = InputHandler()

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0  # Get time elapsed in seconds

        # Update timers if game is active
        if not game_state.is_game_over and not renderer.animation.is_animating():
            if game_state.current_turn == "white":
                game_state.white_time -= dt
                if game_state.white_time <= 0:
                    game_state.white_time = 0
                    game_state.timeout_winner = "black"
            else:
                game_state.black_time -= dt
                if game_state.black_time <= 0:
                    game_state.black_time = 0
                    game_state.timeout_winner = "white"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                    break
                elif event.key == pygame.K_r:
                    # Restart game
                    board_obj = Board()
                    game_state = GameState(board_obj)
                    input_handler.reset()
                    continue
                elif event.key == pygame.K_ESCAPE:
                    input_handler.reset()
                    continue

            # Skip input if animation is playing or game is over
            if renderer.animation.is_animating():
                continue

            # Handle input events
            action = input_handler.handle_event(event, game_state)

            if action and action["type"] == "move":
                start = action["start"]
                end = action["end"]

                # Check what piece will be moved (before process_move changes it)
                sr, sc = start
                er, ec = end
                moving_piece = game_state.board[sr][sc]
                captured_piece = game_state.board[er][ec]

                # Process the move through game state
                success = game_state.process_move(start, end)

                if success:
                    # Animate the move
                    def draw_sidebar():
                        renderer.draw_sidebar(screen, game_state)

                    renderer.animation.animate_move(
                        screen, renderer.board_ui, renderer.piece_ui,
                        moving_piece, start, end,
                        game_state.board, game_state, clock,
                        draw_callback=draw_sidebar
                    )

                    # Capture effect
                    if captured_piece:
                        renderer.animation.animate_capture_effect(
                            screen, end, clock
                        )

        screen.fill(COLOR_BG)
        renderer.draw(screen, game_state, input_handler)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
