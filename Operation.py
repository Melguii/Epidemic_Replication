import re
from datetime import datetime


class Operation:
    def __init__(self, index, value, type):
        self.index = index
        self.value = value
        self.type = type

    def to_string(self):
        return "w(" + str(self.index) + "," + str(self.value) + ")"


def parse_transaction(transaction):
    operations = []
    array_operations = transaction.split(' ')

    i = 0
    for op in array_operations:
        if "r" in op:
            operations.append(Operation(re.search(r'[0-9]+', op).group(i), -1, 'r'))
        elif "w" in op:
            write_operations = re.findall(r'[0-9]+', op)
            val0 = int(write_operations[0])
            val1 = int(write_operations[1])
            operations.append(Operation(val0, val1, 'w'))

    return operations


def add_log(path, values):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    f = open(path, "a")
    f.write(path + "\t" + current_time + "\tValues: " + str(values) + "\n")
    f.close()
