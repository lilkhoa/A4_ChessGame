import json
import random
import time
import asyncio

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        # Players will be represented by their (reader, writer) object, mainly writer for broadcast
        self.players = [] # list of asyncio.StreamWriter objects

        # Adding fields for manageing game time
        self.white_time = 300.0
        self.black_time = 300.0
        self.current_turn = "white"
        self.last_move_time = None
        self.is_running = False
        self.timeout_task = None

    def add_player(self, writer):
        if len(self.players) < 2:
            self.players.append(writer)
            return True
        return False

    def remove_player(self, writer):
        if writer in self.players:
            self.players.remove(writer)
        
        if len(self.players) < 2:
            self.stop_game()

    async def broadcast(self, message, sender_writer=None):
        """
        Sends a JSON message + newline to all players in the room except the sender.
        """
        msg_str = json.dumps(message) + "\n"
        msg_bytes = msg_str.encode("utf-8")
        
        for w in self.players:
            if w != sender_writer:
                try:
                    w.write(msg_bytes)
                    await w.drain()
                except Exception as e:
                    print(f"[Room {self.room_id}] Failed to send data to a client: {e}")

    @staticmethod
    def generate_room_id():
        """
        Generates a 6-digit string ID securely.
        """
        return str(random.randint(100000, 999999))
    
    def start_game(self):
        self.is_running = True
        self.last_move_time = time.time()

        if self.timeout_task is None:
            self.timeout_task = asyncio.create_task(self.check_timeout_loop())

    def stop_game(self):
        """
            Stop the timer (when GameOver, Timeour or opponent disconnection)
        """
        self.is_running = False
        if self.timeout_task:
            self.timeout_task.cancel()
            self.timeout_task = None

    def process_time_for_move(self):
        """
            Compute the time elapsed since the last move and update and change the current turn
        """
        if not self.is_running or self.last_move_time is None:
            return
        
        now = time.time()
        elapsed = now - self.last_move_time
        self.last_move_time = now
        
        if self.current_turn == "white":
            self.white_time = max(0.0, self.white_time - elapsed)
            self.current_turn = "black"
        else:
            self.back_time = max(0.0, self.back_time - elapsed)
            self.current_turn = "white"                
    
    async def check_timeout_loop(self):
        """
            Loops in background to check if any layers has run out of time
        """
        try:
            while self.is_running:
                await asyncio.sleep(1.0)
                if not self.is_running or self.last_move_time is None:
                    continue

                now = time.time()
                elapsed = now - self.last_move_time
                if self.current_turn == "white" and (self.white_time - elapsed <= 0):
                    timeout_player = "white"
                    self.white_time = 0.0
                elif self.current_turn == "black" and (self.black_time - elapsed <= 0):
                    timeout_player = "black"
                    self.black_time = 0.0

                if timeout_player:
                    print(f"[Room {self.room_id}] Player {timeout_player} timed out!")
                    self.stop_game()
                    winner = "black" if timeout_player == "white" else "white"

                    await self.broadcast({
                        "action": "timeout",
                        "room_id": self.room_id,
                        "winner": winner,
                        "timeout_player": timeout_player,
                    }, sender_writer=None)  # sender_writer=None to notify both players
                    break
        except asyncio.CancelledError:
            pass  # Task was cancelled, just exit the loop