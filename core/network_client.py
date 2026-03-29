import socket
import json
import threading
import queue

class NetworkClient:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.msg_queue = queue.Queue()
        self.running = False
        
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3.0) # timeout for connection attempt
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None) # reset timeout to blocking for background thread
            self.connected = True
            self.running = True
            
            # Start background thread to listen for server messages
            threading.Thread(target=self._listen, daemon=True).start()
            return True
        except Exception as e:
            print(f"NetworkClient Connection Failed: {e}")
            return False
            
    def _listen(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    print("NetworkClient: Server closed connection.")
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.msg_queue.put(json.loads(line))
            except Exception as e:
                if self.running:
                    print(f"NetworkClient Error: {e}")
                break
        self.connected = False
                
    def send(self, data_dict):
        if self.connected:
            try:
                msg = json.dumps(data_dict) + "\n"
                self.sock.send(msg.encode('utf-8'))
            except Exception as e:
                print(f"NetworkClient Send Error: {e}")
                self.connected = False
                
    def get_events(self):
        events = []
        while not self.msg_queue.empty():
            events.append(self.msg_queue.get())
        return events
        
    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
