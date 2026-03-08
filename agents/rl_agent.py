import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from ai.model import ChessNet
from agents.base_agent import BaseAgent

class RLAgent(BaseAgent):
    def __init__(self, name="Double_DQN_Bot", model_path=None, device='cpu'):
        super().__init__(name)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        
        self.model = ChessNet().to(self.device)
        self.target_model = ChessNet().to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001)
        self.criterion = nn.SmoothL1Loss() 
        
        self.memory = deque(maxlen=5000) 
        self.batch_size = 64
        self.gamma = 0.99
        self.epsilon = 1.0
        
    def board_to_tensor(self, board_obj):
        state = np.zeros((12, 8, 8), dtype=np.float32)
        type_map = {'pawn': 0, 'knight': 1, 'bishop': 2, 'rook': 3, 'queen': 4, 'king': 5}
        for r in range(8):
            for c in range(8):
                piece = board_obj.get_piece(r, c)
                if piece and piece.name in type_map:
                    idx = type_map[piece.name]
                    if piece.color == 'black': idx += 6
                    state[idx][r][c] = 1
        return state

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def get_move(self, board, game_state, color):
        legal_moves = self.get_legal_moves(board, game_state, color)
        if not legal_moves: return None
        
        if random.random() < self.epsilon:
            return random.choice(legal_moves)

        state = self.board_to_tensor(board)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state_t)

        best_move = None
        max_q = -float('inf')
        for move in legal_moves:
            idx = (move.start_row * 8 + move.start_col) * 64 + (move.end_row * 8 + move.end_col)
            if q_values[0][idx] > max_q:
                max_q = q_values[0][idx]
                best_move = move
        return best_move

    def replay(self):
        if len(self.memory) < self.batch_size: return
        
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

    
        current_q = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        with torch.no_grad():
            next_actions = self.model(next_states).argmax(1).unsqueeze(1)
            next_q = self.target_model(next_states).gather(1, next_actions).squeeze(1)
            target_q = rewards + (self.gamma * next_q * (1 - dones))

        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()

    def update_target_network(self):
        self.target_model.load_state_dict(self.model.state_dict())