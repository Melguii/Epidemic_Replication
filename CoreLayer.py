import socket
from threading import Thread, Lock
import argparse
import time
import re
import json

values = {}
update_counter = 0

last_op = None
mutex = Lock()

layer1_node = None
server_a = None
server_b = None


# TODO: Encara falta testejar codi i tb canviar algunes cosetes
# TODO: Falta que mitjançant alguna operació es tanquin els recursos

class Operation:
    def __init__(self, index, value, type):
        self.index = index
        self.value = value
        self.type = type

    def to_string(self):
        return "w(" + self.index + "," + self.value + ")"


def parse_transaction(transaction):
    operations = []
    array_operations = transaction.split(' ')

    for op in array_operations:
        if "r" in op:
            operations.append(Operation(re.search(r'[0-9]+', transaction).group(), -1, 'r'))
        elif "w" in op:
            write_operations = re.findall(r'[0-9]+', op)
            operations.append(Operation(int(write_operations[0]), int(write_operations[1]), 'w'))

    return operations


def dedicated_server_client(dsc_socket):
    global update_counter
    global last_op
    transaction = dsc_socket.recv(1024).decode()
    operations = parse_transaction(transaction)

    for op in operations:
        if op.type is 'r':
            string = "INDEX -> [" + op.index + "]; VALUE -> [" + values[op.index] + "]"
            dsc_socket.send(string.encode())
        else:
            values[op.index] = op.value
            update_counter += 1
            last_op = op.to_string()
            # Enviem l'operació als nodes veïns
            mutex.release()
            # Esperem que finalitzi la comuncació entre veïns
            mutex.acquire()

    dsc_socket.send("ACK")
    dsc_socket.close()


def update_layer1_node():
    global update_counter

    if layer1_node is not None and 10 == update_counter:
        update_counter = 0
        json_dict = json.dumps(values)
        layer1_node.send(json_dict.encode())
    elif 10 == update_counter:
        update_counter = 0


def dedicated_server_neighbour(dsn_socket):
    global update_counter
    while True:
        transaction = dsn_socket.recv(1024).decode()
        op = re.findall(r'[0-9]+', transaction)

        values[op[0]] = op[1]
        update_counter += 1

        # Mirem si hem d'actualitzar Layer1
        update_layer1_node()
        dsn_socket.send("ACK")


def server(host, port):
    connection_counter = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            while True:
                (clientsocket, address) = s.accept()
                if connection_counter < 2:
                    with Thread(target=dedicated_server_neighbour(clientsocket), args=(1,)) as dedicated_server_thread:
                        dedicated_server_thread.start()
                else:
                    with Thread(target=dedicated_server_client(clientsocket), args=(1,)) as dedicated_server_thread:
                        dedicated_server_thread.start()


# Encarregat d'anar fer transaccions sobre el node i enviar als altres CL la instrucció
def client_node(host, servers_to_connect, l1_port):
    global server_a, server_b, layer1_node
    global update_counter

    # Ens connectem als CoreLayer veïns
    server_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_a.connect((host, servers_to_connect[0]))

    server_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_b.connect((host, servers_to_connect[1]))

    # Ens connectem al node L1 veï
    if l1_port > 0:
        layer1_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        layer1_node.connect((host, l1_port))

    mutex.acquire()
    while True:
        mutex.acquire()

        # Enviem als altres CoreLayers el procés d'escriptura que s'ha executat en aquest
        server_a.send(last_op.encode())
        server_b.send(last_op.encode())

        # Esperem resposta "ACK" del altres servidor abans de continuar
        if server_a.recv(1024).decode() == "ACK":
            pass
        if server_b.recv(1024).decode() == "ACK":
            pass

        # Mirem si hem d'actualitzar Layer1
        update_layer1_node()
        mutex.release()


def identify_server_port(self_server_port):
    if self_server_port == 8001:
        return [8002, 8003], 0
    elif self_server_port == 8002:
        return [8001, 8003], 9001
    else:
        return [8001, 8002], 9002


if __name__ == "__main__":
    # Parsejem arguments i fitxer de transaccions. (o be llegirles totes
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=float, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 8000 + args.id
    cl_ports, l1_port = identify_server_port(PORT)

    with Thread(target=server(HOST, PORT), args=(2,)) as server_cl:
        server_cl.start()
    time.sleep(15)  # Temps per obrir els altres core layers servers
    with Thread(target=client_node(HOST, cl_ports, l1_port), args=(3,)).start() as client_cl:
        client_cl.start()
