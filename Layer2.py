import os
import socket
import time
from threading import Thread
import argparse
import json
import signal

import Operation as Op

values = {}
dedicated_server = None
close = False


def dedicated_server_layer1(dsl1_socket):
    global values, name, close
    while True:
        new_values = dsl1_socket.recv(1024).decode()
        if new_values == "":
            close = True
            return
        values = {int(k): int(v) for k, v in json.loads(new_values).items()}
        Op.add_log("Logs/" + name + ".txt", values)
        print("Layer 2 actualitzat!")
        print(values)


def dedicated_server_client(dsc_socket):
    global close
    transaction = dsc_socket.recv(1024).decode()
    if transaction == "":
        close = True
        return

    operations = Op.parse_transaction(transaction)
    for op in operations:
        string = "INDEX -> [" + str(op.index) \
                 + "]; VALUE -> [" + str(values.get(int(op.index), "POSICIÓ BUIDA")) + "]"
        dsc_socket.send(string.encode())
        time.sleep(0.3)

    dsc_socket.send("ACK".encode())
    dsc_socket.close()


def server(host, port):
    global dedicated_server, close
    dedicated_server = []
    connection_counter = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("ES PERMETEN NOVES CONNEXIONS...")
        while True:
            if close is True:
                break
            (clientsocket, address) = s.accept()
            if connection_counter < 1:
                dedicated_server.append(Thread(target=dedicated_server_layer1, args=(clientsocket,)))
            else:
                dedicated_server.append(Thread(target=dedicated_server_client, args=(clientsocket,)))
            dedicated_server[connection_counter].start()
            connection_counter += 1


def close_node(signum, stack):
    os.kill(os.getpid(), signal.SIGTERM)


if __name__ == "__main__":
    global server_cl, name
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=int, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 10000 + args.id
    l1_port = 9002
    name = "C1" if PORT == 10001 else "C2"

    server_cl = Thread(target=server, args=(HOST, PORT,))
    server_cl.start()

    signal.signal(signal.SIGINT, close_node)
    while True:
        signal.pause()
