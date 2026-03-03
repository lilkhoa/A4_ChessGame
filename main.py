from controllers.game_controller import GameController
from agents import RandomAgent, MinimaxAgent


def main():
    game = GameController()
    
    # Enable time control: 5 minutes per player
    game.enable_clock(time_per_player=300.0)
    
    # Enable AI opponent (Minimax, depth 3)
    ai = MinimaxAgent(name="Minimax Bot", depth=3)
    game.enable_ai(ai_color='black', ai_agent=ai)

    # Start the app (menu → game → pause cycle)
    game.run()


if __name__ == "__main__":
    main()
