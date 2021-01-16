import socket
from threading import Thread, Lock
import argparse
import time
import re

values = {}
update_counter = 0  # todo: protegir update_counter
#mutex = Lock() -> en cas que obrisim més d'un client hauriem de protegir les variables globals


class Operation:
    def __init__(self, index, value, type):
        self.index = index
        self.value = value
        self.type = type


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


def dedicated_server(socket):
    transaction = socket.recv(1024).decode()
    operations = parse_transaction(transaction)

    for op in operations:
        if op.type is 'r':
            string = "INDEX", op.index, "VALUE ->", values[op.index]
            socket.send(string.encode())
        else:
            values[op.index] = op.value
            update_counter += 1

            # TODO: enviar als veïns
            if 10 == update_counter:
                update_counter = 0

    socket.send("ACK")
    socket.close()


def server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            while True:
                (clientsocket, address) = s.accept()
                Thread(target=dedicated_server(clientsocket), args=(1,)).start()


# Encarregat d'anar fer transaccions sobre el node i enviar als altres CL la instrucció
def client(host, servers_to_connect, l1_port):
    # Ens connectem als CoreLayer veïns
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_a:
        server_a.connect((host, servers_to_connect[0]))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_b:
        server_b.connect((host, servers_to_connect[1]))


def identify_server_port(self_server_port):
    if self_server_port == 8001:
        return [8002, 8003], 0
    elif self_server_port == 8002:
        return [8001, 8003], 9001
    else:
        return [8001, 8002], 9002


if __name__ == "__main__":
    core_layers = None

    # Parsejem arguments i fitxer de transaccions. (o be llegirles totes
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=float, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 8000 + args.id
    cl_ports, l1_port = identify_server_port(PORT)

    server = Thread(target=server(HOST, PORT), args=(2,)).start()
    time.sleep(15)  # Temps per obrir els altres core layers servers
    client = Thread(target=client(HOST, cl_ports, l1_port), args=(4,)).start()
