from controllers.game_controller import GameController
from agents.rl_agent import RLAgent 

def main():
    game = GameController()
    
    game.enable_clock(time_per_player=300.0) 

    model_path = "checkpoints/chess_v1_10.pth" 
    
    ai = RLAgent(name="Deep Q-Bot", model_path=model_path)
    
    game.enable_ai(ai_color='black', ai_agent=ai)

    game.run()

if __name__ == "__main__":
    main()