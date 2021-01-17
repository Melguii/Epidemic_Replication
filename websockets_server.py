import asyncio
import time

import websockets
import signal
import os


def close_server(signum, stack):
    time.sleep(1)
    asyncio.get_event_loop().stop()
    os.kill(os.getpid(), signal.SIGTERM)


signal.signal(signal.SIGINT, close_server)


async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")


start_server = websockets.serve(hello, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
