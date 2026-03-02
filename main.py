from controllers.game_controller import GameController


def main():
    game = GameController()
    
    # Optional: Enable time control (uncomment to use)
    game.enable_clock(time_per_player=300.0)  # 5 minutes per player
    
    # Optional: Enable AI (uncomment when AI is implemented)
    # Example:
    #   from agents import RandomAgent
    #   ai = RandomAgent("Easy Bot")
    #   game.enable_ai(ai_color='black', ai_agent=ai)
    #
    # For more AI examples, see: example_with_ai.py
    
    # Start the game loop
    game.run()


if __name__ == "__main__":
    main()
