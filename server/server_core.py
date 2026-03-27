import asyncio
import json
from .room import Room

class ChessServer:
    def __init__(self):
        self.rooms = {} # Maps room_id (string) -> Room object
        self.client_rooms = {} # Maps writer object -> room_id (string)
        
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"[Server] Client connected: {addr}")
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    print(f"[Server] Client disconnected: {addr}")
                    break
                
                message = data.decode("utf-8").strip()
                if not message:
                    continue
                    
                print(f"[{addr}] Received: {message}")
                try:
                    payload = json.loads(message)
                    await self.process_message(payload, writer)
                except json.JSONDecodeError:
                    print(f"[{addr}] Received invalid JSON.")
                    await self.send_error(writer, "Invalid JSON format.")
        except ConnectionResetError:
            print(f"[Server] Connection reset by client: {addr}")
        except Exception as e:
            print(f"[Server] Error handling client {addr}: {e}")
        finally:
            await self.disconnect_client(writer)
            
    async def process_message(self, payload, writer):
        """
        Routes the parsed JSON payload to the corresponding action.
        """
        action = payload.get("action")
        
        if action == "create_room":
            room_id = Room.generate_room_id()
            while room_id in self.rooms:
                room_id = Room.generate_room_id()
                
            new_room = Room(room_id)
            self.rooms[room_id] = new_room
            new_room.add_player(writer)
            self.client_rooms[writer] = room_id
            
            await self.send_message(writer, {
                "action": "room_created",
                "room_id": room_id
            })
            print(f"[Server] Room {room_id} created by {writer.get_extra_info('peername')}")
            
        elif action == "join_room":
            room_id = payload.get("room_id")
            if room_id in self.rooms:
                room = self.rooms[room_id]
                if len(room.players) < 2:
                    room.add_player(writer)
                    self.client_rooms[writer] = room_id
                    
                    # Target color logic can be improved, but usually creator is white and joiner is black
                    await self.send_message(writer, {
                        "action": "room_joined",
                        "room_id": room_id,
                        "color": "black" 
                    })
                    
                    # Notify player 1 that the opponent joined
                    await room.broadcast({
                        "action": "opponent_joined",
                        "room_id": room_id,
                        "color": "white"
                    }, sender_writer=writer)
                    
                    print(f"[Server] Client joined room {room_id}")
                else:
                    await self.send_error(writer, "Room is full.")
            else:
                await self.send_error(writer, f"Room {room_id} does not exist.")
                
        elif action in ["move", "chat", "resign", "draw_offer", "draw_accept"]:
            # Route generic game events/actions to the opponent in the same room
            room_id = self.client_rooms.get(writer)
            if room_id in self.rooms:
                room = self.rooms[room_id]
                await room.broadcast(payload, sender_writer=writer)
            else:
                await self.send_error(writer, "You are not in a room.")

    async def disconnect_client(self, writer):
        """
        Handles sudden disconnection by removing the client from memory
        and notifying their opponent.
        """
        room_id = self.client_rooms.get(writer)
        if room_id and room_id in self.rooms:
            room = self.rooms[room_id]
            room.remove_player(writer)
            
            # Notify remaining player
            if len(room.players) > 0:
                await room.broadcast({
                    "action": "opponent_disconnected"
                })
            else:
                # Discard the room safely from server memory
                print(f"[Server] Room {room_id} is empty. Destroying.")
                del self.rooms[room_id]
                
        # Clean from mapping
        if writer in self.client_rooms:
            del self.client_rooms[writer]
            
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

    async def send_message(self, writer, message):
        msg_str = json.dumps(message) + "\n"
        try:
            writer.write(msg_str.encode("utf-8"))
            await writer.drain()
        except Exception as e:
            print(f"[Server] Error sending direct message: {e}")

    async def send_error(self, writer, error_msg):
        await self.send_message(writer, {"action": "error", "message": error_msg})
