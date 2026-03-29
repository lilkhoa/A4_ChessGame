# Chess Game

A fully-featured chess game built with Python and Pygame, featuring AI opponents with multiple difficulty levels, complete chess rules implementation, and an intuitive graphical interface.

## Installation

### Quick Install (Recommended)

Using uv package manager:

```bash
# Install uv
pip install uv

# Install game dependencies
cd d:\Game\code\A4_ChessGame
uv pip install -e .
```

### Alternative: Using pip

```bash
pip install -e .
```

## How to Play

### Starting the Game

Run the main game:

```bash
python main.py
```

### Starting the Server (Online Multiplayer)

To host online games, you need to run the backend socket server parallel to the game:

```bash
python server/main.py
```
This starts the matchmaking service for generating and joining rooms.

The game will open with a main menu where you can:
- Start a new game (Player vs Player or Player vs AI)
- Choose AI difficulty (Easy, Medium, Hard)
- Continue a saved game
- Configure time controls

## AI Agents

### RandomAgent
- Makes completely random legal moves
- Instant response
- Suitable for beginners

### MinimaxAgent
- Uses minimax algorithm with alpha-beta pruning
- Evaluates positions using piece-square tables
- Configurable search depth:
  - Depth 2: Fast, decent play (~0.1s per move)
  - Depth 3: Stronger, slower (~1-3s per move)
  - Depth 4+: Very strong but slow (5s+ per move)

### RLAgent (Deep Q-Learning)
- Neural network-based agent
- Trained using reinforcement learning
- Uses chess_v1_10.pth checkpoint

## Game Rules

Standard FIDE chess rules are implemented:

**Piece Movement:**
- All pieces move according to official chess rules
- Pawns can move two squares on first move
- Pawns promote to Queen when reaching the opposite end

**Special Moves:**
- Castling: King moves two squares toward rook (kingside or queenside)
- En Passant: Capture a pawn that just moved two squares
- Pawn Promotion: Automatically promotes to Queen

**Win Conditions:**
- Checkmate: Opponent's king is in check with no legal moves
- Timeout: Opponent runs out of time (with clock enabled)

**Draw Conditions:**
- Stalemate: No legal moves but king is not in check
- Threefold Repetition: Same position occurs three times
- Fifty-Move Rule: 50 moves without pawn move or capture
- Insufficient Material: Not enough pieces to checkmate (e.g., King vs King)

## Project Structure

```
A4_ChessGame/
├── agents/              AI agent implementations
├── ai/                  Neural network models for RL agent
├── assets/              Images, sounds, and other assets
├── checkpoints/         Trained model checkpoints
├── controllers/         Game flow and turn management
├── core/                Chess logic, rules, and board state
├── pieces/              Chess piece classes
├── ui/                  Rendering and input handling
├── tests/               Test scripts for agents
├── config.py            Game configuration
├── main.py              Main entry point
└── pyproject.toml       Dependencies
```

## Credits

Educational project demonstrating chess game implementation with AI agents. Built with Python, Pygame, and PyTorch.
