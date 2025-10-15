import asyncio
import websockets

async def test_websocket():
    url = "ws://localhost:8000/ws/dashboard"
    async with websockets.connect(url) as ws:
        await ws.send("Hello from client!")
        response = await ws.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
