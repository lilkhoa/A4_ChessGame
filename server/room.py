import json
import random

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        # Players will be represented by their (reader, writer) object, mainly writer for broadcast
        self.players = [] # list of asyncio.StreamWriter objects

    def add_player(self, writer):
        if len(self.players) < 2:
            self.players.append(writer)
            return True
        return False

    def remove_player(self, writer):
        if writer in self.players:
            self.players.remove(writer)

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
