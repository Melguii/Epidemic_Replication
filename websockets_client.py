import asyncio
import json
import os
import signal
import time

import websockets

name = ""
values = {}


def update_node_info_event():
    global name, values
    return json.dumps({"type": name, "value": str(values)})


async def client():
    uri = "ws://localhost:5678"
    async with websockets.connect(uri) as websocket:
        json_msg = update_node_info_event()
        await websocket.send(json_msg)
        await asyncio.sleep(5)


def send_to_web(node, hashmap):
    global name, values
    name = node
    values = hashmap
    asyncio.get_event_loop().run_until_complete(client())


if __name__ == '__main__':
    send_to_web("A1", {4: 5})

"""""
class WbClient:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def update_node_info_event(self):
        return json.dumps({"type": self.name, "value": str(self.values)})

    async def client(self, websocket, path):
        uri = "ws://localhost:5678"
        async with websockets.connect(uri) as websocket:
            json_msg = self.update_node_info_event()
            await websocket.send(json_msg)

    def send_to_web(self):
        asyncio.get_event_loop().run_until_complete(self.client())
"""""
