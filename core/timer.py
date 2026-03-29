class Timer:
    """
    Local timer management for chess games.
    """
    
    def __init__(self, white_time_seconds=300.0, black_time_seconds=300.0, increment_seconds=0.0):
        self.white_time = float(white_time_seconds)
        self.black_time = float(black_time_seconds)
        self.increment = float(increment_seconds)
        self.current_turn = 'white'
        self.is_running = False
        self.timeout_flag = None
    
    def tick(self, delta_time):
        """Decrement the current player's time."""
        if not self.is_running:
            return
        if self.current_turn == 'white':
            self.white_time -= delta_time
            if self.white_time <= 0:
                self.white_time = 0
                self.timeout_flag = 'white'
        else:
            self.black_time -= delta_time
            if self.black_time <= 0:
                self.black_time = 0
                self.timeout_flag = 'black'
    
    def switch_turn(self):
        """Switch to the opponent's turn."""
        if self.increment > 0:
            if self.current_turn == 'white':
                self.white_time += self.increment
            else:
                self.black_time += self.increment
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
    
    def sync(self, white_time, black_time):
        """Synchronize with server time."""
        self.white_time = float(white_time)
        self.black_time = float(black_time)
        self.timeout_flag = None
    
    def start(self):
        self.is_running = True
    
    def stop(self):
        self.is_running = False
    
    def pause(self):
        self.is_running = False
    
    def resume(self):
        self.is_running = True
    
    def reset(self, white_time=300.0, black_time=300.0):
        self.white_time = float(white_time)
        self.black_time = float(black_time)
        self.current_turn = 'white'
        self.is_running = False
        self.timeout_flag = None
    
    def is_timeout(self):
        return self.timeout_flag
    
    def get_remaining_time(self, color):
        return self.white_time if color == 'white' else self.black_time
    
    def __repr__(self):
        return (f"Timer(white={self.white_time:.1f}s, black={self.black_time:.1f}s, "
                f"turn={self.current_turn}, running={self.is_running})")
