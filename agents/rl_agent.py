import torch
import numpy as np
from agents.base_agent import BaseAgent
from ai.model import ChessNet 

class RLAgent(BaseAgent):
    def __init__(self, name="Deep Q-Bot", model_path=None, device='cpu'):
        super().__init__(name)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        
        self.model = ChessNet().to(self.device)
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                print(f"--- Đã load thành công model RL: {model_path} ---")
            except Exception as e:
                print(f"--- Lỗi load model: {e}. AI sẽ dùng trọng số ngẫu nhiên! ---")
        
        self.model.eval() 

    def board_to_tensor(self, board_obj):
        """
        Chuyển đổi Board thành Tensor 12x8x8 dựa trên thuộc tính .name 
        giống như MinimaxAgent sử dụng.
        """
        state = np.zeros((12, 8, 8), dtype=np.float32)
        
        type_map = {
            'pawn': 0,
            'knight': 1,
            'bishop': 2,
            'rook': 3,
            'queen': 4,
            'king': 5
        }

        for r in range(8):
            for c in range(8):
                piece = board_obj.get_piece(r, c)
                if piece and piece.name in type_map:
                    idx = type_map[piece.name]
                    if piece.color == 'black':
                        idx += 6
                    state[idx][r][c] = 1
                    
        return state

    def get_move(self, board, game_state, color):
        """
        Hàm chính để GameController gọi lấy nước đi.
        """
        legal_moves = self.get_legal_moves(board, game_state, color)
        if not legal_moves:
            return None

        state = self.board_to_tensor(board)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            q_values = self.model(state_t)

        best_move = None
        max_q = -float('inf')

        for move in legal_moves:

            start_idx = move.start_row * 8 + move.start_col
            end_idx = move.end_row * 8 + move.end_col
            move_idx = start_idx * 64 + end_idx
            
            q_val = q_values[0][move_idx].item()
            
            if q_val > max_q:
                max_q = q_val
                best_move = move

        if best_move:
            print(f"AI {self.name} quyết định đi: {best_move} (Q-Value: {max_q:.4f})")
        
        return best_move