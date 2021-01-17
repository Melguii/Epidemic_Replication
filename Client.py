import argparse
import socket
import random
import re
import time


def port_to_connect(layer):
    if 0 == layer:
        return random.randint(8001, 8003)
    elif 1 == layer:
        return random.randint(9001, 9002)
    else:
        return random.randint(10001, 10002)


def detect_type_transaction(transaction):
    if "<" in transaction:
        transaction_type = 'r'
        layer = int(re.search('<(.*)>', transaction).group(1))
    else:
        transaction_type = 'w'
        layer = 0

    return transaction_type, layer


def client(host, transaction):
    # Parsejem transaccio
    transaction_type, layer = detect_type_transaction(transaction)

    # Decidim el port a qui enviar la transacció
    port = port_to_connect(layer)

    print("\nNOVA TRANSACCIÓ!:\t" + transaction + "ENVIANT A...\t" + str(port))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as epidemic_client:
        epidemic_client.connect((host, port))
        epidemic_client.send(transaction.encode())
        data = epidemic_client.recv(1024).decode()

        while data != "ACK":
            print(data)
            data = epidemic_client.recv(1024).decode()
        print("TRANSACCIÓ FINALITZADA...")


def process_input(filename):
    transactions = []

    for line in open(filename, 'r'):
        transactions.append(line)

    for t in transactions:
        print(str(t))

    return transactions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("file", type=str, help="Fitxer a processar")
    args = parser.parse_args()
    transactions = process_input(args.file)

    time.sleep(5)

    for transaction in transactions:
        client('127.0.0.1', transaction)

    print("\nFINALITZANT TRANSACCIONS...")