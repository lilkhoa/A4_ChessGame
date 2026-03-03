import chess
import torch
import os
from ai.model import ChessNet
from ai.agent import ChessAgent

def get_material_value(board):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    total = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = values[piece.piece_type]
            total += val if piece.color == chess.WHITE else -val
    return total

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = ChessAgent(device=device)
    agent.init_model(ChessNet())
    
    num_episodes = 11
    save_interval = 10
    
    if not os.path.exists('checkpoints'): os.makedirs('checkpoints')

    for ep in range(num_episodes):
        board = chess.Board()
        state = agent.get_state(board)
        total_reward = 0
        
        while not board.is_game_over():
            # Lưu giá trị quân số trước khi đi
            old_material = get_material_value(board)
            
            move = agent.select_move(board)
            action_idx = move.from_square * 64 + move.to_square
            board.push(move)
            
            next_state = agent.get_state(board)
            done = board.is_game_over()
            
            # Tính Reward
            reward = 0
            new_material = get_material_value(board)
            reward += (new_material - old_material) * 10 # Thưởng khi ăn quân
            
            if board.is_checkmate():
                reward += 100
            elif done: # Hòa
                reward -= 10
                
            agent.update_model(state, action_idx, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            if len(board.move_stack) > 200: break # Tránh game quá dài

        print(f"Episode {ep} | Reward: {total_reward} | Epsilon: {agent.epsilon:.3f}")
        
        if ep % save_interval == 0:
            torch.save(agent.model.state_dict(), f"checkpoints/chess_v1_{ep}.pth")

if __name__ == "__main__":
    train()