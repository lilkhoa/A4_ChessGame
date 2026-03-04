import os
import random
import torch
import torch.nn as nn
import torch.optim as optim
from ai.model import ChessNet
from agents.rl_agent import RLAgent
from core.board import Board
from core.game_state import GameState
from core.rules import Rules

def get_material_value(board):
    values = {'pawn': 1, 'knight': 3, 'bishop': 3, 'rook': 5, 'queen': 9, 'king': 0}
    total = 0
    for r in range(8):
        for c in range(8):
            piece = board.get_piece(r, c)
            if piece:
                val = values.get(piece.name, 0)
                total += val if piece.color == 'white' else -val
    return total

def is_game_over(board, game_state, rules):
    return any([
        rules.is_checkmate(board, game_state, 'white'),
        rules.is_checkmate(board, game_state, 'black'),
        rules.is_stalemate(board, game_state, 'white'),
        rules.is_stalemate(board, game_state, 'black'),
        rules.is_draw(board, game_state, 'white')
    ])

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    agent = RLAgent(name="Trainer_Bot", device=device)
    agent.model = ChessNet().to(device)
    agent.optimizer = optim.Adam(agent.model.parameters(), lr=0.001)
    agent.criterion = nn.MSELoss()
    agent.epsilon = 1.0
    agent.epsilon_decay = 0.995
    agent.epsilon_min = 0.05
    
    rules = Rules()
    os.makedirs('checkpoints', exist_ok=True)

    for ep in range(11):
        board = Board()
        game_state = GameState(board, rules)
        state = agent.board_to_tensor(board)
        total_reward = 0
        
        while not is_game_over(board, game_state, rules):
            color = game_state.current_turn
            old_mat = get_material_value(board)
            legal_moves = agent.get_legal_moves(board, game_state, color)
            
            if not legal_moves:
                break
                
            move = random.choice(legal_moves) if random.random() < agent.epsilon else agent.get_move(board, game_state, color)
            action_idx = (move.start_row * 8 + move.start_col) * 64 + (move.end_row * 8 + move.end_col)
            
            game_state.process_move((move.start_row, move.start_col), (move.end_row, move.end_col))
            
            next_state = agent.board_to_tensor(board)
            done = is_game_over(board, game_state, rules)
            
            new_mat = get_material_value(board)
            mat_diff = new_mat - old_mat
            reward = (-mat_diff if color == 'black' else mat_diff) * 10 
            
            if rules.is_checkmate(board, game_state, 'white') and color == 'black':
                reward += 100
            elif rules.is_checkmate(board, game_state, 'black') and color == 'white':
                reward += 100
            elif done:
                reward -= 10
                
            agent.model.train()
            state_t = torch.FloatTensor(state).unsqueeze(0).to(device)
            next_state_t = torch.FloatTensor(next_state).unsqueeze(0).to(device)
            
            current_q = agent.model(state_t)[0][action_idx]
            with torch.no_grad():
                next_q = agent.model(next_state_t).max()
            
            target_q = reward + (0.99 * next_q * (1 - int(done)))
            loss = agent.criterion(current_q, target_q)
            
            agent.optimizer.zero_grad()
            loss.backward()
            agent.optimizer.step()
            
            state = next_state
            total_reward += reward
            
            if len(game_state.move_log) > 200: 
                break

        agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)
        print(f"Ep {ep} | Reward: {total_reward:.1f} | Eps: {agent.epsilon:.3f} | Moves: {len(game_state.move_log)}")
        
        if ep % 10 == 0:
            torch.save(agent.model.state_dict(), f"checkpoints/chess_v1_{ep}.pth")

if __name__ == "__main__":
    train()