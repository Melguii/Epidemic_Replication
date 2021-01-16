import socket
from threading import Thread, Lock
import argparse
import time
import re
import socket
from threading import Thread
import argparse
import time
import json

values = {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("id", type=float, help="Instància del servidor")
    args = parser.parse_args()

    HOST = '127.0.0.1'
    PORT = 10000 + args.id
    l1_port = 9002

    with Thread(target=server(HOST, PORT), args=(2,)) as server_cl:
        server_cl.start()
    time.sleep(25)  # Temps per obrir els altres core layers servers
    with Thread(target=client_node(HOST, l1_port), args=(2,)).start() as client_cl:
        client_cl.start()