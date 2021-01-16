import socket
from threading import Thread, Lock
import argparse
import time
import json
import signal

values = {}
update_timer = 10
mutex = Lock()

core_layer_node = None


def client_node(host, cl_port):
    global core_layer_node

    # Ens connectem als CoreLayer veïns
    core_layer_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    core_layer_node.connect((host, cl_port))

    #TODO: Aqui configurem l'alarma per actualitzar L2


if __name__ == "__main__":
    # Parsejem arguments i fitxer de transaccions. (o be llegirles totes
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=float, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 9000 + args.id
    cl_port = 8002 if PORT == 9001 else 8003

    with Thread(target=server(HOST, PORT), args=(2,)) as server_cl:
        server_cl.start()
    time.sleep(20)  # Temps per obrir els altres core layers servers
    with Thread(target=client_node(HOST, cl_port), args=(2,)).start() as client_cl:
        client_cl.start()
