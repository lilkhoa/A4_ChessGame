import torch
import torch.optim as optim
import torch.nn as nn
import numpy as np
import random

class ChessAgent:
    def __init__(self, device='cpu', lr=0.001):
        self.device = device
        self.model = None 
        self.optimizer = None
        self.criterion = nn.MSELoss()
        self.epsilon = 1.0 
        self.epsilon_decay = 0.9995
        self.epsilon_min = 0.05

    def init_model(self, model):
        self.model = model.to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

    def get_state(self, board):
        state = np.zeros((12, 8, 8), dtype=np.float32)
        for square, piece in board.piece_map().items():
            rank, file = divmod(square, 8)
            idx = (piece.piece_type - 1) if piece.color else (piece.piece_type + 5)
            state[idx][rank][file] = 1
        return state

    def select_move(self, board):
        legal_moves = list(board.legal_moves)
        if random.random() < self.epsilon:
            return random.choice(legal_moves)
        
        state = self.get_state(board)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(state_t)
        
        best_move = legal_moves[0]
        max_q = -float('inf')
        for move in legal_moves:
            idx = move.from_square * 64 + move.to_square
            if outputs[0][idx] > max_q:
                max_q = outputs[0][idx]
                best_move = move
        return best_move

    def update_model(self, state, action_idx, reward, next_state, done):
        self.model.train()
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        next_state_t = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
        
        current_q = self.model(state_t)[0][action_idx]
        with torch.no_grad():
            next_q = self.model(next_state_t).max()
        
        target_q = reward + (0.99 * next_q * (1 - int(done)))
        
        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay