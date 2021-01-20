import asyncio
import datetime
import json
import random
import time
from threading import Thread

import websockets
import signal
import os

STATE = {"value": 0}

USERS = set()
"""""
def state_event():
    return json.dumps({"type": "state", **STATE})


def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.add(websocket)
    await notify_users()


async def unregister(websocket):
    USERS.remove(websocket)
    await notify_users()


async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "minus":
                STATE["value"] -= 1
                await notify_state()
            elif data["action"] == "plus":
                STATE["value"] += 1
                await notify_state()
    finally:
        await unregister(websocket)


start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()



"""""
connected = set()


def close_server(signum, stack):
    time.sleep(1)
    asyncio.get_event_loop().stop()
    os.kill(os.getpid(), signal.SIGTERM)


async def server(websocket, path):
    connected.add(websocket)
    while True:
        try:
            node_info = await websocket.recv()
            print(node_info)
            await asyncio.wait([ws.send(node_info) for ws in connected])
        finally:
            connected.remove(websocket)


signal.signal(signal.SIGINT, close_server)
start_server = websockets.serve(server, "localhost", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

"""""

async def server(websocket, path):
    while True:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        await websocket.send(now)
        await asyncio.sleep(random.random() * 3)


<ul>
            <div class="A1">Node A1: {}</div>
            <div class="A2">Node A2: {}</div>
            <div class="A3">Node A3: {}</div>
            <div class="B1">Node B1: {}</div>
            <div class="B2">Node B2: {}</div>
            <div class="C1">Node C1: {}</div>
            <div class="C2">Node C2: {}</div>
        </ul>
        <script>
            var a1 = document.querySelector('.A1'),
                a2 = document.querySelector('.A2'),
                a3 = document.querySelector('.A3'),
                b1 = document.querySelector('.B1'),
                b2 = document.querySelector('.B2'),
                c1 = document.querySelector('.C1'),
                c2 = document.querySelector('.C2'),
                websocket = new WebSocket("ws://127.0.0.1:8765/");

            websocket.onmessage = function (event) {
                data = JSON.parse(event.data);
                console.log(data)
                switch (data.type) {
                    case "A1":
                        a1.textContent = data.value;
                        break;
                    case "A2":
                        a2.textContent = data.value;
                        break;
                    default:
                        console.error(
                            "unsupported event", data);
                }
            };
        </script>
"""""
