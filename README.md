# A4 - Chess Game

A fully-featured chess game implemented in Python and Pygame with AI agents support. Play against friends locally or challenge AI opponents with different difficulty levels.

## Features

- ✅ **Complete Chess Rules**: All standard chess rules including castling, en passant, pawn promotion, check, checkmate, and stalemate
- ✅ **Draw Detection**: Automatic detection of threefold repetition, fifty-move rule, and insufficient material
- ⏱️ **Time Controls**: Optional chess clock with configurable time limits
- 🤖 **AI Agents**: Play against Random or Minimax AI opponents
- 🎨 **Graphical Interface**: Clean Pygame-based UI with piece dragging and move highlighting
- 🔄 **Game Reset**: Press R to restart the game at any time
- 📊 **Move History**: Track all moves and game state throughout the match

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you haven't already
pip install uv

# Navigate to project directory
cd d:\Game\code\A4_ChessGame

# Install dependencies
uv pip install -e .

# Optional: Install development dependencies
uv pip install --group dev -e .
```

### Using pip

```bash
# Install dependencies from pyproject.toml
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

## Quick Start

### Human vs Human

```bash
python main.py
```

This starts a standard two-player game with a 5-minute timer for each player.

### Human vs AI

Edit `main.py` to enable AI:

```python
from controllers.game_controller import GameController
from agents import RandomAgent, MinimaxAgent

def main():
    game = GameController()
    game.enable_clock(time_per_player=300.0)  # 5 minutes per side
    
    # Choose your AI agent:
    # Easy: RandomAgent
    ai = RandomAgent(name="Easy Bot")
    
    # OR Medium-Hard: MinimaxAgent (depth 2-4)
    # ai = MinimaxAgent(name="Strategic Bot", depth=3)
    
    game.enable_ai(ai_color='black', ai_agent=ai)
    game.run()

if __name__ == "__main__":
    main()
```

Or run the examples:

```bash
python example_with_ai.py
```

## Controls

| Key/Action | Description |
|------------|-------------|
| **Mouse Click** | Select and move pieces |
| **Mouse Drag** | Drag pieces to move |
| **R** | Reset/Restart game |
| **ESC** | Quit game |

## AI Agents

### Available Agents

1. **RandomAgent**: Selects random legal moves
   - Difficulty: Very Easy
   - Speed: Instant
   - Usage: `RandomAgent(name="Easy Bot")`

2. **MinimaxAgent**: Uses minimax algorithm with alpha-beta pruning
   - Difficulty: Configurable by depth
     - Depth 2: Easy (~0.1s per move)
     - Depth 3: Medium (~1-3s per move) ⭐ **Recommended**
     - Depth 4: Hard (~5-10s per move)
     - Depth 5+: Very Hard (30s+ per move)
   - Speed: Varies by depth
   - Usage: `MinimaxAgent(name="Strategic Bot", depth=3)`

### Adding New Agents

To create a custom agent:

```python
from agents import BaseAgent

class MyAgent(BaseAgent):
    def get_move(self, board, game_state, color):
        # Your AI logic here
        legal_moves = self.get_legal_moves(board, game_state, color)
        # Return a Move object
        return legal_moves[0] if legal_moves else None
```

Then register it in `agents/__init__.py`:

```python
from .my_agent import MyAgent

__all__ = ['BaseAgent', 'RandomAgent', 'MinimaxAgent', 'MyAgent']
```

## Project Structure

```
A4_ChessGame/
├── agents/              # AI agent implementations
│   ├── base_agent.py    # Abstract base class for all agents
│   ├── random_agent.py  # Random move selection agent
│   └── minimax_agent.py # Minimax with alpha-beta pruning
├── controllers/         # Game flow management
│   ├── game_controller.py   # Main game loop and UI bridge
│   └── turn_controller.py   # Turn management and clock
├── core/                # Core game logic
│   ├── board.py         # Board state and piece management
│   ├── game_state.py    # Game state tracking
│   ├── move.py          # Move representation
│   ├── rules.py         # Chess rules engine
│   └── utils.py         # Helper functions
├── pieces/              # Chess piece implementations
│   ├── base_piece.py    # Abstract piece class
│   ├── pawn.py
│   ├── rook.py
│   ├── knight.py
│   ├── bishop.py
│   ├── queen.py
│   └── king.py
├── ui/                  # User interface
│   ├── renderer.py      # Game rendering
│   ├── board_ui.py      # Board visualization
│   ├── piece_ui.py      # Piece sprites
│   └── input_handler.py # Mouse/keyboard input
├── assets/              # Game assets (images, sounds)
├── config.py            # Game configuration
├── main.py              # Entry point for human vs human
├── example_with_ai.py   # Examples with AI agents
└── pyproject.toml       # Project dependencies (uv compatible)
```

## Configuration

Edit `config.py` to customize:

- Board size and colors
- Window dimensions
- Frame rate (FPS)
- UI colors and fonts

## Development

### Installing Development Dependencies

```bash
# Using uv (recommended)
uv pip install --group dev -e .

# Using pip with optional dependencies
pip install -e ".[training]"  # For AI training dependencies
```

### Running Tests

```bash
# Run tests (when implemented)
pytest tests/
```

### Code Formatting

```bash
# Format code with black
black .

# Lint with ruff
ruff check .
```

## Game Rules

This implementation follows standard FIDE chess rules:

- **Standard Moves**: All pieces move according to official rules
- **Special Moves**: Castling (kingside/queenside), en passant capture, pawn promotion (to Queen)
- **Check & Checkmate**: King cannot move into check; checkmate ends the game
- **Stalemate**: No legal moves without being in check results in a draw
- **Draw Conditions**:
  - Threefold repetition
  - Fifty-move rule (50 moves without pawn move or capture)
  - Insufficient material (K vs K, K+N vs K, K+B vs K, etc.)
- **Time Control**: Optional chess clock with timeout loss

## Troubleshooting

### AI Not Moving

Make sure you've called `game.enable_ai()` before `game.run()` and that the AI color matches the player you want the AI to control.

### Slow Performance

If the MinimaxAgent is too slow, reduce the search depth:
```python
ai = MinimaxAgent(depth=2)  # Faster but weaker
```

### Import Errors

Make sure all dependencies are installed:
```bash
uv pip install -e .
```

## License

This project is for educational purposes.

## Contributing

Feel free to fork and improve! Potential enhancements:

- [ ] Add more advanced AI agents (Neural Networks, MCTS)
- [ ] Add multiplayer online support
- [ ] Implement opening book for AI
- [ ] Add move hints for players
- [ ] Save/load game functionality
- [ ] Add sound effects and animations
- [ ] Support for chess variants (Chess960, etc.)

## Credits

Developed as part of A4 coursework. Built with Python and Pygame.