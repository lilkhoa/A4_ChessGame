import pygame
import torch
import sys

# Import Core
from core.board import Board
from core.game_state import GameState
from core.rules import Rules
from agents.rl_agent import RLAgent

# Import UI
from ui.renderer import Renderer
from ui.input_handler import InputHandler

# Import Config (Dự phòng nếu thiếu config)
try:
    from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
except ImportError:
    print("Không tìm thấy config.py. Đang sử dụng kích thước mặc định.")
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS = 850, 600, 60

# Đường dẫn Model
MODEL_WHITE_PATH = "checkpoints/ddqn_chess_0.pth"
MODEL_BLACK_PATH = "checkpoints/ddqn_chess_100.pth"
DELAY_MS = 500  # Thời gian chờ giữa các nước đi

class AIBattleUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI vs AI: Professional UI Battle")
        self.clock = pygame.time.Clock()
        
        # 1. Khởi tạo Logic Game
        self.board = Board()
        self.rules = Rules()
        self.game_state = GameState(self.board, self.rules)
        self._inject_missing_attributes(self.game_state)
        
        # 2. Khởi tạo UI Components
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        
        # 3. Khởi tạo AI
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.agent_white = RLAgent(name="RL_White", model_path=MODEL_WHITE_PATH, device=device)
        self.agent_white.epsilon = 0.0
        
        self.agent_black = RLAgent(name="RL_Black", model_path=MODEL_BLACK_PATH, device=device)
        self.agent_black.epsilon = 0.0

    def _inject_missing_attributes(self, state):
        """
        Bơm thêm các thuộc tính mà Renderer yêu cầu để vẽ Sidebar và Overlay.
        """
        if not hasattr(state, 'white_time'): state.white_time = 0
        if not hasattr(state, 'black_time'): state.black_time = 0
        if not hasattr(state, 'timeout_winner'): state.timeout_winner = None
        if not hasattr(state, 'draw_reason'): state.draw_reason = None
        if not hasattr(state, 'is_checkmate'): state.is_checkmate = False
        if not hasattr(state, 'is_draw'): state.is_draw = False

    def update_game_status(self):
        """Cập nhật trạng thái checkmate/draw cho Renderer."""
        self.game_state.is_checkmate = (
            self.rules.is_checkmate(self.board, self.game_state, 'white') or 
            self.rules.is_checkmate(self.board, self.game_state, 'black')
        )
        
        if self.rules.is_stalemate(self.board, self.game_state, 'white') or \
           self.rules.is_stalemate(self.board, self.game_state, 'black'):
            self.game_state.is_draw = True
            self.game_state.draw_reason = 'stalemate'
        elif self.rules.is_draw(self.board, self.game_state, 'white'):
            self.game_state.is_draw = True
            self.game_state.draw_reason = 'unknown'

    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            game_over = self.game_state.is_checkmate or self.game_state.is_draw or self.game_state.timeout_winner

            if not game_over:
                color = self.game_state.current_turn
                current_agent = self.agent_white if color == 'white' else self.agent_black
                
                # AI tính toán
                move = current_agent.get_move(self.board, self.game_state, color)
                
                if move:
                    # 1. Đi quân trên bàn cờ
                    self.game_state.process_move((move.start_row, move.start_col), (move.end_row, move.end_col))
                    
                    # 2. QUAN TRỌNG: Tự động chuyển lượt cho bên kia
                    self.game_state.current_turn = 'black' if color == 'white' else 'white'
                    
                    # 3. Cập nhật trạng thái game
                    self.update_game_status()
                    
                    # Render và chờ
                    self.renderer.draw(self.screen, self.game_state, self.input_handler)
                    pygame.display.flip()
                    pygame.time.wait(DELAY_MS)
                else:
                    self.game_state.is_draw = True 
            
            self.renderer.draw(self.screen, self.game_state, self.input_handler)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        import sys
        sys.exit()

if __name__ == "__main__":
    game = AIBattleUI()
    game.run()