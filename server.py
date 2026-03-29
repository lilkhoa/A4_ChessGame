import socket
import threading
import json
import logging
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'
PORT = 5055

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rooms = {}  # room_id -> {"players": [], "turn": "white"}
        self.clients = {}  # conn -> {"id": uuid, "room": room_id, "color": "white"|"black", "nickname": str}
        self.lock = threading.Lock()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            logging.info(f"Server started on {self.host}:{self.port}")
            
            while True:
                conn, addr = self.server_socket.accept()
                logging.info(f"New connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, conn, addr):
        client_id = str(uuid.uuid4())
        
        with self.lock:
            self.clients[conn] = {"id": client_id, "room": None, "color": None, "nickname": f"Player_{client_id[:4]}"}

        try:
            # Send initial welcome containing client ID
            self.send_to_client(conn, {"type": "WELCOME", "client_id": client_id})

            while True:
                # Receive size prefix or directly data (we'll use direct for simplicity, size up to 1024)
                # In production, a protocol with length prefix is better.
                data = conn.recv(1024)
                if not data:
                    break
                
                try:
                    message_str = data.decode('utf-8').strip()
                    # A single recv might contain multiple JSON messages separated by newlines if sent too fast
                    messages = message_str.split('\n')
                    for msg_str in messages:
                        if not msg_str:
                            continue
                        msg = json.loads(msg_str)
                        self.process_message(conn, msg)
                except json.JSONDecodeError:
                    logging.warning(f"Received invalid JSON from {addr}: {data}")
                except Exception as e:
                    logging.error(f"Error processing message from {addr}: {e}")
                    
        except ConnectionResetError:
            logging.info(f"Client {addr} disconnected abruptly.")
        except Exception as e:
            logging.error(f"Client handling error for {addr}: {e}")
        finally:
            self.disconnect_client(conn)

    def process_message(self, conn, msg):
        msg_type = msg.get("type")
        logging.info(f"Received {msg_type} from {self.clients[conn]['id']}")
        
        if msg_type == "CREATE_ROOM":
            self.handle_create_room(conn)
        elif msg_type == "JOIN_ROOM":
            room_id = msg.get("room_id")
            self.handle_join_room(conn, room_id)
        elif msg_type == "MOVE":
            self.handle_move(conn, msg)
        elif msg_type == "LEAVE_ROOM":
            self.handle_leave_room(conn)

    def send_to_client(self, conn, msg):
        try:
            data = json.dumps(msg) + "\n"
            conn.sendall(data.encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed to send to client {self.clients.get(conn, {}).get('id', 'Unknown')}: {e}")

    def broadcast_to_room(self, room_id, msg, exclude_conn=None):
        with self.lock:
            if room_id not in self.rooms:
                return
            
            for player_conn in self.rooms[room_id]["players"]:
                if player_conn != exclude_conn:
                    self.send_to_client(player_conn, msg)

    def handle_create_room(self, conn):
        with self.lock:
            # Generate a 4-digit room code
            room_id = str(uuid.uuid4())[:4].upper()
            while room_id in self.rooms:
                room_id = str(uuid.uuid4())[:4].upper()

            self.rooms[room_id] = {
                "players": [conn],
                "state": "waiting"
            }
            
            self.clients[conn]["room"] = room_id
            self.clients[conn]["color"] = "white"

        self.send_to_client(conn, {
            "type": "ROOM_CREATED",
            "room_id": room_id,
            "color": "white"
        })
        logging.info(f"Room {room_id} created by {self.clients[conn]['id']}")

    def handle_join_room(self, conn, room_id):
        if not room_id:
            self.send_to_client(conn, {"type": "ERROR", "message": "Room ID cannot be empty"})
            return
            
        room_id = room_id.upper()

        with self.lock:
            if room_id not in self.rooms:
                self.send_to_client(conn, {"type": "ERROR", "message": "Room not found"})
                return

            room = self.rooms[room_id]
            if len(room["players"]) >= 2:
                self.send_to_client(conn, {"type": "ERROR", "message": "Room is full"})
                return

            # Add player to room
            room["players"].append(conn)
            room["state"] = "playing"
            
            self.clients[conn]["room"] = room_id
            # Determine color (opposite of first player)
            first_player = room["players"][0]
            first_color = self.clients[first_player]["color"]
            assigned_color = "black" if first_color == "white" else "white"
            self.clients[conn]["color"] = assigned_color

        # Tell player they joined
        self.send_to_client(conn, {
            "type": "ROOM_JOINED",
            "room_id": room_id,
            "color": assigned_color
        })

        # Notify the room the game is starting
        time.sleep(0.1) # Small delay to ensure client is ready
        self.broadcast_to_room(room_id, {
            "type": "GAME_START",
            "message": "Both players connected. Game starts!"
        })
        logging.info(f"Client {self.clients[conn]['id']} joined room {room_id} as {assigned_color}")

    def handle_move(self, conn, msg):
        room_id = self.clients[conn].get("room")
        if not room_id:
            return
            
        # Broadcast the move to the other player in the room
        self.broadcast_to_room(room_id, {
            "type": "MOVE",
            "start": msg.get("start"),
            "end": msg.get("end"),
            "promotion": msg.get("promotion"),
            "color": self.clients[conn]["color"]
        }, exclude_conn=conn)

    def handle_leave_room(self, conn):
        room_id = self.clients[conn].get("room")
        if not room_id:
            return

        with self.lock:
            if room_id in self.rooms:
                if conn in self.rooms[room_id]["players"]:
                    self.rooms[room_id]["players"].remove(conn)
                
                # If room is empty, delete it
                if not self.rooms[room_id]["players"]:
                    del self.rooms[room_id]
                    logging.info(f"Room {room_id} deleted (empty)")
                else:
                    # Notify remaining player
                    self.broadcast_to_room(room_id, {
                        "type": "OPPONENT_DISCONNECTED",
                        "message": "Opponent left the room."
                    })
                    self.rooms[room_id]["state"] = "waiting"
            
            self.clients[conn]["room"] = None
            self.clients[conn]["color"] = None

    def disconnect_client(self, conn):
        self.handle_leave_room(conn)
        with self.lock:
            if conn in self.clients:
                del self.clients[conn]
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    server = Server(HOST, PORT)
    server.start()
