import sys
import os
import pygame

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.game_controller import GameController
from agents.random_agent import RandomAgent
from agents.minimax_agent import MinimaxAgent
from agents.rl_agent import RLAgent


def print_menu():
    """Display the agent selection menu."""
    print("\n" + "="*60)
    print("       CHESS AGENT TESTING - HUMAN VS AI")
    print("="*60)
    print("\nSelect an opponent:")
    print("  1. Random Agent    - Plays random legal moves")
    print("  2. Minimax Agent   - Uses minimax with alpha-beta pruning")
    print("  3. RL Agent        - Deep Q-Learning agent (chess_v1_10.pth)")
    print("  4. Exit")
    print("\nEnter your choice (1-4): ", end='')


def create_agent(choice):
    """
    Create and return the selected agent.
    
    Args:
        choice (str): The user's menu selection
        
    Returns:
        BaseAgent: The selected agent instance, or None if invalid/exit
    """
    if choice == '1':
        print("\nInitializing Random Agent...")
        return RandomAgent(name="Random Bot")
    
    elif choice == '2':
        print("\nInitializing Minimax Agent...")
        print("Enter search depth (recommended 2-4, default 3): ", end='')
        depth_input = input().strip()
        depth = int(depth_input) if depth_input.isdigit() else 3
        return MinimaxAgent(name=f"Minimax Bot (depth {depth})", depth=depth)
    
    elif choice == '3':
        print("\nInitializing RL Agent...")
        checkpoint_path = os.path.join('checkpoints', 'chess_v1_10.pth')
        
        if not os.path.exists(checkpoint_path):
            print(f"ERROR: Checkpoint not found at {checkpoint_path}")
            print("Please ensure the checkpoint file exists.")
            return None
        
        return RLAgent(name="Deep Q-Bot", model_path=checkpoint_path)
    
    elif choice == '4':
        print("\nExiting...")
        return None
    
    else:
        print("\nInvalid choice. Please select 1-4.")
        return None


def select_player_color():
    """
    Let the user choose their color.
    
    Returns:
        str: 'white' or 'black'
    """
    while True:
        print("\nSelect your color:")
        print("  1. White (you play first)")
        print("  2. Black (AI plays first)")
        print("\nEnter your choice (1-2): ", end='')
        
        choice = input().strip()
        
        if choice == '1':
            return 'white'
        elif choice == '2':
            return 'black'
        else:
            print("Invalid choice. Please select 1 or 2.")


def configure_time_control():
    """
    Let the user choose time control settings.
    
    Returns:
        tuple: (enable_clock, minutes_per_side) or (False, 0) for no clock
    """
    print("\nEnable time control?")
    print("  1. Yes - Set time limit")
    print("  2. No  - Play without time limit")
    print("\nEnter your choice (1-2): ", end='')
    
    choice = input().strip()
    
    if choice == '1':
        print("\nEnter minutes per side (e.g., 5, 10, 15): ", end='')
        minutes_input = input().strip()
        minutes = int(minutes_input) if minutes_input.isdigit() else 10
        return (True, minutes)
    else:
        return (False, 0)


def run_test_game(agent, player_color, time_settings):
    """
    Run a test game with the selected agent.
    
    Args:
        agent (BaseAgent): The AI agent to play against
        player_color (str): 'white' or 'black' for the human player
        time_settings (tuple): (enable_clock, minutes_per_side)
    """
    print("\n" + "="*60)
    print(f"Starting game: YOU ({player_color.upper()}) vs {agent.name}")
    print("="*60)
    
    enable_clock, minutes = time_settings
    if enable_clock:
        print(f"Time control: {minutes} minutes per side")
    else:
        print("No time limit")
    
    print("\nControls:")
    print("  - Click to select and move pieces")
    print("  - ESC to pause/menu")
    print("  - The AI will move automatically on its turn")
    print("\nStarting game window...")
    
    # Initialize pygame
    pygame.init()
    
    # Create game controller
    controller = GameController()
    
    # Reset game to fresh state (bypassing menu)
    controller._reset_game()
    
    # Configure AI based on player color
    ai_color = 'black' if player_color == 'white' else 'white'
    controller.enable_ai(ai_color, ai_agent=agent)
    
    # Configure time control if enabled
    if enable_clock:
        controller.turn_controller.enable_clock(minutes * 60)
    
    # Play game start sound
    controller.sound_manager.play_game_start()
    controller.sound_manager.reset_time_warnings()
    
    # Bypass the main menu by setting app_state directly to "playing"
    controller.app_state = "playing"
    
    # Start the game
    print(f"\n{'='*60}")
    print("GAME STARTED - Good luck!")
    print(f"{'='*60}\n")
    
    controller.run()
    
    # Game finished
    print("\n" + "="*60)
    print("Game ended. Returning to menu...")
    print("="*60)


def main():
    """Main entry point for the agent testing script."""
    print("\n" + "="*60)
    print("  CHESS AI AGENT TESTING SUITE")
    print("  Test human vs. different AI agents")
    print("="*60)
    
    while True:
        # Display menu and get agent selection
        print_menu()
        choice = input().strip()
        
        # Create the selected agent
        agent = create_agent(choice)
        
        # Exit if user chose exit or agent creation failed
        if agent is None:
            if choice == '4':
                break
            continue
        
        # Get player color preference
        player_color = select_player_color()
        
        # Get time control settings
        time_settings = configure_time_control()
        
        # Run the test game
        try:
            run_test_game(agent, player_color, time_settings)
        except KeyboardInterrupt:
            print("\n\nGame interrupted by user.")
        except Exception as e:
            print(f"\n\nError during game: {e}")
            import traceback
            traceback.print_exc()
        
        # Ask if user wants to play again
        print("\nPlay another game? (y/n): ", end='')
        again = input().strip().lower()
        if again not in ['y', 'yes']:
            break
    
    print("\nThank you for testing!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
