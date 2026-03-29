import asyncio
import os
import sys

# Ensure this module can access parent directory files if needed later
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server_core import ChessServer

async def main():
    HOST = '0.0.0.0'
    PORT = 8888
    
    chess_server = ChessServer()
    
    server = await asyncio.start_server(
        chess_server.handle_client, HOST, PORT)

    addr = server.sockets[0].getsockname()
    print(f'=== Chess Multiplayer Server running on {addr} ===')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Shutting down gracefully...")
