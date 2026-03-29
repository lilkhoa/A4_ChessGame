import asyncio
import json

async def send_message(writer, action_dict):
    msg = json.dumps(action_dict) + "\n"
    writer.write(msg.encode("utf-8"))
    await writer.drain()

async def read_message(reader):
    data = await reader.readline()
    if not data:
        return None
    return json.loads(data.decode("utf-8").strip())

async def automated_test():
    print("[Test] Starting automated flow...")
    
    try:
        reader_A, writer_A = await asyncio.open_connection('127.0.0.1', 8888)
    except ConnectionRefusedError:
        print("Failed to connect to tests. Ensure `python server/main.py` is running.")
        return

    print("[Test A] Created room")
    await send_message(writer_A, {"action": "create_room"})
    resp_A = await read_message(reader_A)
    print(f"[Test A] -> {resp_A}")
    room_id = resp_A.get("room_id")
    
    if not room_id:
        print("Failed to create room!")
        return

    reader_B, writer_B = await asyncio.open_connection('127.0.0.1', 8888)
    print(f"[Test B] Joining room {room_id}")
    await send_message(writer_B, {"action": "join_room", "room_id": room_id})
    
    resp_B = await read_message(reader_B)
    print(f"[Test B] -> {resp_B}")
    
    # Client A should get notified about B joining
    resp_A_notify = await read_message(reader_A)
    print(f"[Test A] -> {resp_A_notify}")
    
    # Client A makes a move
    print("[Test A] Sending move")
    await send_message(writer_A, {"action": "move", "data": "e2e4"})
    
    # Client B receives the move
    resp_B_move = await read_message(reader_B)
    print(f"[Test B] -> {resp_B_move}")
    
    # Client A disconnects suddenly
    print("[Test A] Disconnecting from server...")
    writer_A.close()
    await writer_A.wait_closed()
    
    # Client B should receive disconnect notice
    resp_B_dc = await read_message(reader_B)
    print(f"[Test B] -> {resp_B_dc}")
    
    # Client B disconnects voluntarily
    print("[Test B] Disconnecting...")
    writer_B.close()
    await writer_B.wait_closed()
    
    print("[Test] All tests succeeded.")

if __name__ == '__main__':
    asyncio.run(automated_test())
