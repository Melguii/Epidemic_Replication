import socket
from sched import scheduler
from threading import Thread, Lock
import argparse
import time
import re
import json
import signal
import os

import asyncio

import websockets

import Operation as Op

values = {}
update_counter = 0
first_iteration = True
name = ""

last_op = None
mutex = Lock()
blocked = Lock()

dedicated_server = None

server_a = None
server_b = None
layer1_node = None
close = False


def dedicated_server_client(dsc_socket):
    global update_counter, last_op, values, first_iteration
    global mutex, blocked, close
    transaction = dsc_socket.recv(1024).decode()
    if transaction == "":
        dsc_socket.close()
        close = True
        return

    operations = Op.parse_transaction(transaction)
    print("NOVA TRANSACCIó DETECTADA!")

    for op in operations:
        if op.type is 'r':
            string = "INDEX -> [" + str(op.index) \
                     + "]; VALUE -> [" + str(values.get(int(op.index), "POSICIÓ BUIDA")) + "]"
            dsc_socket.send(string.encode())
            time.sleep(0.3)
        else:
            # Bloquejem Lock()
            if first_iteration is True:
                first_iteration = False
                blocked.acquire()

            # Processem a la vegada que enviem l'operació d'escriptura als nodes veïns (active replication)
            values[op.index] = op.value
            last_op = op.to_string()
            # Enviem l'operació als nodes veïns
            mutex.release()
            blocked.acquire()

    dsc_socket.send("ACK".encode())
    dsc_socket.close()


# Aquí actualitzem la Layer 1
def update_layer1_node():
    global update_counter, layer1_node, values, last_op

    # Cada vegada que cridem la funció, vol dir que s'ha executat una nova escriptura
    update_counter += 1
    Op.add_log("Logs/" + name + ".txt", values)

    if layer1_node is not None and 10 == update_counter:
        update_counter = 0
        json_dict = json.dumps(values)
        layer1_node.send(json_dict.encode())
    elif 10 == update_counter:
        update_counter = 0


def dedicated_server_neighbour(dsn_socket):
    global update_counter, values, update_counter, close
    print("NOVA CONNEXIÓ DE SERVIDOR ENTRANT!")

    while True:
        # Quan es tanca, el recv sempre rep trama buida (no hem salta SIGPIPE)
        operation = dsn_socket.recv(1024).decode()
        if operation == "":
            close = True
            return

        # Actualitzem valors d'aquest node.
        op = re.findall(r'[0-9]+', operation)
        values[int(op[0])] = int(op[1])

        # Mirem si hem d'actualitzar Layer1
        update_layer1_node()
        dsn_socket.send("ACK".encode())


def server(host, port):
    global dedicated_server, close
    dedicated_server = []
    connection_counter = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(5)
        print("ES PERMETEN NOVES CONNEXIONS...")
        while True:
            if close is True:
                break
            (clientsocket, address) = s.accept()
            if connection_counter < 2:
                dedicated_server.append(Thread(target=dedicated_server_neighbour, args=(clientsocket,)))
            else:
                dedicated_server.append(Thread(target=dedicated_server_client, args=(clientsocket,)))
            dedicated_server[connection_counter].start()
            connection_counter += 1


# Encarregat d'anar fer transaccions sobre el node i enviar als altres CL la instrucció
def client_node(host, servers_to_connect, l1_port):
    global server_a, server_b, layer1_node, mutex, blocked, last_op

    # Ens connectem als CoreLayer veïns
    server_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_a.connect((host, servers_to_connect[0]))
    server_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_b.connect((host, servers_to_connect[1]))

    # Ens connectem al node L1 veï
    if l1_port > 0:
        layer1_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        layer1_node.connect((host, l1_port))

    print("CONNEXIONS A SERVIDORS ESTABLERTES")
    mutex.acquire()
    while True:
        mutex.acquire()

        # Enviem als altres CoreLayers el procés d'escriptura que s'ha executat en aquest
        server_a.send(last_op.encode())
        server_b.send(last_op.encode())

        # Esperem resposta "ACK" del altres servidor abans de continuar
        while server_a.recv(1024).decode() != "ACK":
            pass
        while server_b.recv(1024).decode() != "ACK":
            pass

        # Mirem si hem d'actualitzar Layer1
        update_layer1_node()
        blocked.release()


# Websocket server
async def server_wb(websocket, path):
    while True:
        node_info = json.dumps(values)
        await websocket.send(node_info)
        await asyncio.sleep(1)


def start_server(port):
    start = websockets.serve(server_wb, "localhost", port + 3)
    asyncio.get_event_loop().run_until_complete(start)
    asyncio.get_event_loop().run_forever()


# Utils
def close_node(signum, stack):
    global layer1_node, server_a, server_b
    print("FINALITZANT EXECUCIÓ...")
    # Tanquem sockets
    if layer1_node is not None:
        layer1_node.close()
    server_a.close()
    server_b.close()
    asyncio.get_event_loop().stop()
    os.kill(os.getpid(), signal.SIGTERM)


def identify_server_port(self_server_port):
    global name
    if self_server_port == 8001:
        name = "A1"
        return [8002, 8003], 0
    elif self_server_port == 8002:
        name = "A2"
        return [8001, 8003], 9001
    else:
        name = "A3"
        return [8001, 8002], 9002


if __name__ == "__main__":
    global server_cl, client_cl
    # Parsejem arguments i fitxer de transaccions. (o be llegirles totes
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=int, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 8000 + args.id
    cl_ports, l1_port = identify_server_port(PORT)

    server_cl = Thread(target=server, args=(HOST, PORT,))
    server_cl.start()

    time.sleep(2)  # Temps per obrir els altres core layers servers

    client_cl = Thread(target=client_node, args=(HOST, cl_ports, l1_port,))
    client_cl.start()

    signal.signal(signal.SIGINT, close_node)
    start_server(PORT)
