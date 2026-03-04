from controllers.game_controller import GameController
from agents import RandomAgent, MinimaxAgent, RLAgent


def main():
    game = GameController()
    
    # Enable time control: 5 minutes per player
    game.enable_clock(time_per_player=300.0)
    
    # Start the app (menu → game → pause cycle)
    game.run()


if __name__ == "__main__":
    main()
