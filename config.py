ROWS = 8
COLS = 8

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

WHITE = "white"
BLACK = "black"

BOARD_WIDTH = 720
BOARD_HEIGHT = 720

# Internal grid metrics inside the 1920x1920 source image (grid is 1742x1742 at 89,89)
BOARD_SCALE = BOARD_WIDTH / 1920.0
BOARD_OFFSET_X = int(89 * BOARD_SCALE)
BOARD_OFFSET_Y = int(89 * BOARD_SCALE)
BOARD_GRID_SIZE = 1742 * BOARD_SCALE
SQUARE_SIZE = BOARD_GRID_SIZE / 8.0 # Kept as float to avoid compounding pixel errors
PIECE_SIZE = int(SQUARE_SIZE * 0.68) # 80% of previous size
BLACK_ROOK_SIZE = int(SQUARE_SIZE * 0.85) # Keep black rook larger as its sprite is small

# UI Layout
SIDEBAR_WIDTH = 220
WINDOW_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT

# FPS
FPS = 60

# Colors (RGB)
COLOR_LIGHT_SQUARE = (240, 217, 181)
COLOR_DARK_SQUARE = (181, 136, 99)
COLOR_SELECTED = (246, 246, 105, 180)
COLOR_VALID_MOVE = (100, 200, 100, 150)
COLOR_LAST_MOVE = (170, 210, 240, 130)
COLOR_CHECK = (235, 97, 80, 180)
COLOR_BG = (48, 46, 43)
COLOR_SIDEBAR_BG = (39, 37, 34)
COLOR_TEXT_PRIMARY = (255, 255, 255)
COLOR_TEXT_SECONDARY = (186, 186, 186)
COLOR_ACCENT = (129, 182, 76)
COLOR_DANGER = (230, 72, 56)
COLOR_PANEL_BG = (53, 51, 48)
COLOR_BORDER = (68, 66, 63)

# Animation
ANIMATION_DURATION = 0.18  # seconds
ANIMATION_FPS = 60

# Asset paths
import os
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
PIECE_IMAGE_DIR = os.path.join(IMAGE_DIR, "chess-img")
BOARD_IMAGE_PATH = os.path.join(IMAGE_DIR, "chess-board.jpg")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")

# MCTS
import math
EXPLORATION_CONST = math.sqrt(2)