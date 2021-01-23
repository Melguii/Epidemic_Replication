import asyncio
import datetime
import os
import socket
from threading import Thread, Lock
import argparse
import time
import json
import signal

import websockets


import Operation as Op

values = {}
mutex = Lock()

layer2_node1 = None
layer2_node2 = None

dedicated_server = None
server_cl = None
client_cl = None
close = False


# Actualitzem nodes layer 2
def update_layer2(signum, stack):
    global values, layer2_node1, layer2_node2, mutex
    mutex.acquire()
    layer2_node1.send(json.dumps(values).encode())
    layer2_node2.send(json.dumps(values).encode())
    mutex.release()
    signal.alarm(10)


# Inicialitzem nodes L2
def client_node(host, l2_ports):
    global layer2_node1, layer2_node2
    if l2_ports != 0:
        layer2_node1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        layer2_node1.connect((host, l2_ports[0]))
        layer2_node2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        layer2_node2.connect((host, l2_ports[1]))

    print("CONNEXIONS A SERVIDORS ESTABLERTES")


# Aquí el Core Layer Node sobreescriu la info del hashmap
def dedicated_server_core_layer(dscl_socket):
    global values, mutex, close, name
    while True:
        new_values = dscl_socket.recv(1024).decode()
        if new_values == "":
            close = True
            return

        mutex.acquire()
        values = {int(k): int(v) for k, v in json.loads(new_values).items()}
        Op.add_log("Logs/" + name + ".txt", values)
        mutex.release()


def dedicated_server_client(dsc_socket):
    transaction = dsc_socket.recv(1024).decode()
    operations = Op.parse_transaction(transaction)

    for op in operations:
        string = "INDEX -> [" + str(op.index) \
                 + "]; VALUE -> [" + str(values.get(int(op.index), "POSICIÓ BUIDA")) + "]"
        dsc_socket.send(string.encode())
        time.sleep(0.3)

    dsc_socket.send("ACK".encode())
    dsc_socket.close()


def server(host, port):
    global dedicated_server
    dedicated_server = []
    connection_counter = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("ES PERMETEN NOVES CONNEXIONS...")
        while True:
            (clientsocket, address) = s.accept()
            if connection_counter < 1:
                dedicated_server.append(Thread(target=dedicated_server_core_layer, args=(clientsocket,)))
            else:
                dedicated_server.append(Thread(target=dedicated_server_client, args=(clientsocket,)))
            dedicated_server[connection_counter].start()
            connection_counter += 1


def close_node(signum, stack):
    global dedicated_server, server_cl, client_cl
    global layer2_node1, layer2_node2
    # Tanquem sockets
    if layer2_node1 is not None and layer2_node2 is not None:
        layer2_node1.close()
        layer2_node2.close()
    asyncio.get_event_loop().stop()
    os.kill(os.getpid(), signal.SIGTERM)


async def server_wb(websocket, path):
    while True:
        node_info = json.dumps(values)
        await websocket.send(node_info)
        await asyncio.sleep(1)


def start_server(port):
    start = websockets.serve(server_wb, "localhost", port + 2)
    asyncio.get_event_loop().run_until_complete(start)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    global name
    signal.signal(signal.SIGINT, close_node)

    # Parsejem arguments i fitxer de transaccions. (o be llegirles totes
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=int, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 9000 + args.id
    l2_ports = 0 if PORT == 9001 else [10001, 10002]
    name = "B1" if l2_ports == 0 else "B2"

    server_cl = Thread(target=server, args=(HOST, PORT,))
    server_cl.start()

    time.sleep(2)  # Temps per obrir els altres core layers servers

    client_cl = Thread(target=client_node, args=(HOST, l2_ports,))
    client_cl.start()

    # Aquí configurem l'alarma per actualitzar L2
    if l2_ports != 0:
        signal.signal(signal.SIGALRM, update_layer2)
        signal.alarm(10)

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Execució comença: " + current_time)

    signal.signal(signal.SIGINT, close_node)
    start_server(PORT)
