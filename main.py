from controllers.game_controller import GameController
from agents import RandomAgent, MinimaxAgent


def main():
    game = GameController()
    
    # Optional: Enable time control (uncomment to use)
    game.enable_clock(time_per_player=300.0)  # 5 minutes per player
    
    # Optional: Enable AI (uncomment when AI is implemented)
    # Example:
    #   from agents import RandomAgent
    #   ai = RandomAgent("Easy Bot")
    #   game.enable_ai(ai_color='black', ai_agent=ai)

    # Example with MinimaxAgent:    
    ai = MinimaxAgent(name="Minimax Bot", depth=3)
    game.enable_ai(ai_color='black', ai_agent=ai)

    # Start the game loop
    game.run()


if __name__ == "__main__":
    main()
