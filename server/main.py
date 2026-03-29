import asyncio
import os
import sys

# Ensure this module can access parent directory files if needed later
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server_core import ChessServer, DiscoveryProtocol

async def main():
    HOST = '0.0.0.0'
    PORT = 8888
    DISCOVERY_PORT = 8889
    
    chess_server = ChessServer()
    
    # Start UDP Discovery
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DiscoveryProtocol(tcp_port=PORT),
        local_addr=(HOST, DISCOVERY_PORT)
    )
    
    server = await asyncio.start_server(
        chess_server.handle_client, HOST, PORT)

    addr = server.sockets[0].getsockname()
    print(f'=== Chess Multiplayer Server running on {addr} ===')
    print(f'=== Auto-Discovery UDP active on port {DISCOVERY_PORT} ===')

    async with server:
        print(f"[Server] TCP Server is now listening at {addr}")
        print(f"[Server] To stop, press Ctrl+C in this window.")
        try:
            # We use an Event to keep the main task alive indefinitely
            stop_event = asyncio.Event()
            await stop_event.wait() 
        except Exception as e:
            print(f"[Server] Server process encountered an error: {e}")
            raise e

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Shutting down gracefully...")
