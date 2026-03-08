import os
import torch
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
    return any([rules.is_checkmate(board, game_state, 'white'),
                rules.is_checkmate(board, game_state, 'black'),
                rules.is_stalemate(board, game_state, 'white'),
                rules.is_stalemate(board, game_state, 'black'),
                rules.is_draw(board, game_state, 'white')])

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = RLAgent(name="DoubleDQN_Trainer", device=device)
    rules = Rules()
    os.makedirs('checkpoints', exist_ok=True)

    EPSILON_DECAY = 0.95 
    MIN_EPSILON = 0.05
    TARGET_UPDATE_FREQ = 10 
    TOTAL_EPOCHS = 100

    print(f"Bắt đầu huấn luyện trên thiết bị: {device}")

    for ep in range(1, TOTAL_EPOCHS + 1):
        board = Board()
        game_state = GameState(board, rules)
        total_reward = 0
        
        state = agent.board_to_tensor(board)
        
        while not is_game_over(board, game_state, rules):
            current_color = game_state.current_turn
            old_mat = get_material_value(board)
            
            move = agent.get_move(board, game_state, current_color)
            if not move: break
            
            action_idx = (move.start_row * 8 + move.start_col) * 64 + (move.end_row * 8 + move.end_col)
            
            game_state.process_move((move.start_row, move.start_col), (move.end_row, move.end_col))
            
            next_state = agent.board_to_tensor(board)
            done = is_game_over(board, game_state, rules)
            
            new_mat = get_material_value(board)
            mat_diff = new_mat - old_mat
            
            reward = (mat_diff if current_color == 'white' else -mat_diff) * 10
            
            if done:
                if rules.is_checkmate(board, game_state, 'black'): 
                    reward += 100 if current_color == 'white' else -100
                elif rules.is_checkmate(board, game_state, 'white'): 
                    reward += 100 if current_color == 'black' else -100
                else: 
                    reward -= 10 

            agent.remember(state, action_idx, reward, next_state, done)
            agent.replay()
            
            state = next_state
            total_reward += reward
            
            if len(game_state.move_log) > 150: 
                break

        agent.epsilon = max(MIN_EPSILON, agent.epsilon * EPSILON_DECAY)
        
        if ep % TARGET_UPDATE_FREQ == 0:
            agent.update_target_network()

        print(f"Ep {ep:3d}/{TOTAL_EPOCHS} | Reward: {total_reward:6.1f} | Eps: {agent.epsilon:.3f} | Steps: {len(game_state.move_log)}")
        
        if ep % 25 == 0 or ep == TOTAL_EPOCHS:
            torch.save(agent.model.state_dict(), f"checkpoints/ddqn_chess_{ep}.pth")
            print(f"--> Đã lưu mô hình tại epoch {ep}")

if __name__ == "__main__":
    train()