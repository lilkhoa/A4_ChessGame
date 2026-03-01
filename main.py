from controllers.game_controller import GameController


def main():
    game = GameController()
    
    # Optional: Enable time control (uncomment to use)
    game.enable_clock(time_per_player=300.0)  # 5 minutes per player
    
    # Optional: Enable AI (uncomment when AI is implemented)
    # game.enable_ai(ai_color='black', ai_callback=your_ai_function)
    
    # Start the game loop
    game.run()


if __name__ == "__main__":
    main()
