import socket
import threading
import json
import queue
import logging

class NetworkClient:
    """
    Handles background socket communication with the game server.
    Messages received from the server are placed into a thread-safe ThreadQueue,
    which the main GameController can poll every frame.
    """
    def __init__(self):
        self.socket = None
        self.connected = False
        self.message_queue = queue.Queue()
        self.receive_thread = None
        self.client_id = None
        
        self.room_id = None
        self.my_color = None

    def connect(self, host, port):
        """Connect to the server and start listening thread."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # Timeout for connect
            self.socket.connect((host, port))
            self.socket.settimeout(None) # Remove timeout for blocking recv
            self.connected = True
            
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Wait for welcome message to ensure full connection
            while self.client_id is None and self.connected:
                msg = self.poll_message()
                if msg and msg.get('type') == 'WELCOME':
                    self.client_id = msg.get('client_id')
                    return True
                elif msg:
                    # If it's not a WELCOME message but we got *something*, put it back
                    self.message_queue.put(msg)
                import time
                time.sleep(0.05)
            
            return self.client_id is not None
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            self.disconnect()
            return False

    def discover_and_connect_lan(self, timeout=0.8, port=8889):
        """Broadcasts UDP to find a running server on LAN and connects."""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.settimeout(timeout)
        
        print(f"[Client] Searching for server on port {port}...")
        try:
            # Try both global broadcast and localhost to be safe
            udp_socket.sendto(b"CHESS_DISCOVER", ("255.255.255.255", port))
            udp_socket.sendto(b"CHESS_DISCOVER", ("127.0.0.1", port))
            
            while True:
                data, addr = udp_socket.recvfrom(1024)
                msg = data.decode('utf-8')
                if msg.startswith("CHESS_SERVER_TCP:"):
                    tcp_port = int(msg.split(":")[1])
                    server_ip = addr[0]
                    udp_socket.close()
                    print(f"[Client] Discovered server at {server_ip}:{tcp_port}")
                    return self.connect(server_ip, tcp_port)
        except socket.timeout:
            print("[Client] Discovery timeout - no server responded on LAN.")
            # Smart Fallback: If on the same machine, try connecting to localhost directly
            print("[Client] Trying smart fallback to localhost:8888...")
            return self.connect("127.0.0.1", 8888)
        except Exception as e:
            logging.error(f"UDP Discovery error: {e}")
        finally:
            udp_socket.close()
        return False

    def _receive_loop(self):
        """Background thread loop to continuously read from the socket."""
        buffer = ""
        while self.connected:
            try:
                if not self.socket: break
                data = self.socket.recv(1024)
                if not data:
                    logging.info("Server disconnected")
                    self._handle_disconnect()
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            
                            # Intercept some state-altering messages automatically
                            if msg.get('type') in ['ROOM_CREATED', 'ROOM_JOINED', 'GAME_START']:
                                if 'room_id' in msg:
                                    self.room_id = msg.get('room_id')
                                if 'color' in msg:
                                    self.my_color = msg.get('color')
                            
                            self.message_queue.put(msg)
                        except json.JSONDecodeError:
                            logging.error(f"Failed to parse JSON: {line}")
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                # Socket was closed or reset, exit thread silently
                self._handle_disconnect()
                break
            except Exception as e:
                logging.error(f"Socket receive error: {e}")
                self._handle_disconnect()
                break

    def _handle_disconnect(self):
        self.connected = False
        self.message_queue.put({"type": "DISCONNECTED", "message": "Lost connection to server"})
        self.room_id = None
        self.my_color = None

    def disconnect(self):
        """Close connection gracefully."""
        self.connected = False
        if self.socket:
            try:
                self.send({"type": "LEAVE_ROOM"})
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
            self.socket = None
        self.room_id = None
        self.my_color = None

    def send(self, msg_dict):
        """Send a JSON payload to the server."""
        if not self.connected or not self.socket:
            return False
            
        try:
            data = json.dumps(msg_dict) + "\n"
            self.socket.sendall(data.encode('utf-8'))
            return True
        except Exception as e:
            logging.error(f"Send failed: {e}")
            self._handle_disconnect()
            return False

    def poll_message(self):
        """Retrieve the oldest message from the queue, or None if empty."""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    # --- High Level API Methods ---

    def create_room(self):
        self.send({"type": "CREATE_ROOM"})

    def join_room(self, room_id):
        self.send({"type": "JOIN_ROOM", "room_id": room_id})
        
    def send_move(self, start_pos, end_pos, promotion=None):
        self.send({
            "type": "MOVE",
            "start": start_pos,
            "end": end_pos,
            "promotion": promotion
        })
