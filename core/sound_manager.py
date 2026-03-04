import pygame
import os


class SoundManager:
    """
    Centralized sound management class.
    
    Handles loading, playing, and stopping all game sounds including:
    - Background music
    - Move sounds (normal, capture, castle, promotion)
    - Game state sounds (start, end, illegal move)
    - Timer warnings
    """
    
    def __init__(self, sounds_dir='assets/sounds'):
        """
        Initialize the sound manager.
        
        Args:
            sounds_dir: Path to the sounds directory
        """
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.sounds_dir = sounds_dir
        self.sounds = {}
        self.music_playing = False
        
        # Track warning sound to prevent spam
        self.ten_second_warning_played = {'white': False, 'black': False}
        
        # Load all sound files
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all sound files from the sounds directory."""
        sound_files = {
            'bg': 'bg.mp3',
            'capture': 'capture.mp3',
            'castle': 'castle.mp3',
            'game_end': 'game-end.mp3',
            'game_start': 'game-start.mp3',
            'illegal': 'illegal.mp3',
            'move': 'move.mp3',
            'promote': 'promote.mp3',
            'ten_seconds': 'tenseconds.mp3'
        }
        
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(self.sounds_dir, filename)
            try:
                # Background music is handled differently (streamed)
                if sound_name == 'bg':
                    # We'll load this as music, not a sound effect
                    continue
                else:
                    self.sounds[sound_name] = pygame.mixer.Sound(filepath)
            except Exception as e:
                print(f"Warning: Could not load sound '{filename}': {e}")
    
    # ==================== Background Music ====================
    
    def play_background_music(self, loop=True):
        """
        Play background music.
        
        Args:
            loop: If True, loop the music indefinitely
        """
        if self.music_playing:
            return
        
        music_path = os.path.join(self.sounds_dir, 'bg.mp3')
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.3)  # Set volume to 30% to not overpower
            loops = -1 if loop else 0  # -1 means infinite loop
            pygame.mixer.music.play(loops)
            self.music_playing = True
        except Exception as e:
            print(f"Warning: Could not play background music: {e}")
    
    def stop_background_music(self):
        """Stop background music."""
        if self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
    
    def pause_background_music(self):
        """Pause background music (can be resumed later)."""
        if self.music_playing:
            pygame.mixer.music.pause()
    
    def resume_background_music(self):
        """Resume paused background music."""
        if self.music_playing:
            pygame.mixer.music.unpause()
    
    # ==================== Game State Sounds ====================
    
    def play_game_start(self):
        """Play sound when a game starts."""
        self._play_sound('game_start')
    
    def play_game_end(self):
        """Play sound when the game ends."""
        self._play_sound('game_end')
    
    def play_illegal_move(self):
        """Play sound when an illegal move is attempted."""
        self._play_sound('illegal')
    
    # ==================== Move Sounds ====================
    
    def play_move(self):
        """Play sound for a normal move (no capture, castle, or promotion)."""
        self._play_sound('move')
    
    def play_capture(self):
        """Play sound when a piece is captured."""
        self._play_sound('capture')
    
    def play_castle(self):
        """Play sound when castling occurs."""
        self._play_sound('castle')
    
    def play_promotion(self):
        """Play sound when a pawn is promoted."""
        self._play_sound('promote')
    
    # ==================== Timer Warning ====================
    
    def play_ten_second_warning(self, color):
        """
        Play warning sound when a player has less than one minute remaining.
        Only plays once per player per game session.
        
        Args:
            color: 'white' or 'black'
        """
        if not self.ten_second_warning_played.get(color, False):
            self._play_sound('ten_seconds')
            self.ten_second_warning_played[color] = True
    
    def reset_time_warnings(self):
        """Reset time warning tracking (called when starting a new game)."""
        self.ten_second_warning_played = {'white': False, 'black': False}
    
    # ==================== Helper Methods ====================
    
    def _play_sound(self, sound_name):
        """
        Internal method to play a sound effect.
        
        Args:
            sound_name: Name of the sound to play
        """
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Warning: Could not play sound '{sound_name}': {e}")
        else:
            print(f"Warning: Sound '{sound_name}' not loaded")
    
    def set_sound_volume(self, volume):
        """
        Set the volume for all sound effects.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        for sound in self.sounds.values():
            sound.set_volume(volume)
    
    def set_music_volume(self, volume):
        """
        Set the volume for background music.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        pygame.mixer.music.set_volume(volume)
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds (not music)."""
        pygame.mixer.stop()
    
    def cleanup(self):
        """Clean up sound resources."""
        self.stop_background_music()
        self.stop_all_sounds()
        pygame.mixer.quit()
