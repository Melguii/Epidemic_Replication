import argparse
import socket
import random
import re


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
        layer = re.search('<(.*)>', transaction).group(1)
    else:
        transaction_type = 'w'
        layer = 0

    return transaction_type, layer


def client(host, transaction):
    # Parsejem transaccio
    transaction_type, layer = detect_type_transaction(transaction)

    # Decidim el port a qui enviar la transacció
    port = port_to_connect(layer)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as epidemic_client:
        epidemic_client.connect((host, port))
        epidemic_client.send(transaction.encode())
        data = epidemic_client.recv(1024).decode()

        while data != "ACK":
            print(data)
            data = epidemic_client.recv(1024).decode()

        print("TRANSACCIÓ FINALITZADA...")
        epidemic_client.close()


def process_input(filename):
    transactions = []

    for line in open(filename, 'r'):
        transactions.append(line)

    return transactions


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Crear replicació epidèmica")
    parser.add_argument("file", type=str, help="Fitxer a processar")
    args = parser.parse_args()
    transactions = process_input(args.file)

    for transaction in transactions:
        client('127.0.0.1', transaction)

    print("FINALITZANT TRANSACCIONS...")

"""""
    str = "b w(65,89) c"
    array = re.findall(r'[0-9]+', str)
    for i in range(0, len(array)):
        array[i] = int(array[i])
    data = re.search(r'[0-9]+', str).group()
    print(array)
    print(data)
 """""

#TODO: fer un programa que llenci primer tots els nodes i despres el client. Quan el client acabi,
# que pregunti si vol que recarrguem de nou les transaccion o tancar el sistema, llavor que el mateix
# programa (que inicia tots) llenci CTRL + C a cada node, i aquest gestioni el mateix tancament. No cal
# llençar signal a client
