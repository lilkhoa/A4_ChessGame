from controllers.game_controller import GameController


def main():
    game = GameController()
    
    # Enable time control: 10 minutes per player
    game.enable_clock(time_per_player=600.0)
    
    # Start the app (menu → game → pause cycle)
    game.run()


if __name__ == "__main__":
    main()
