'''fiddle file for playing with serialised streaming of data
via ip4 sockets, based upon the example in 
https://github.com/PyTables/PyTables/blob/develop/examples/multiprocess_access_benchmarks.py
'''

import multiprocessing
import os
import random
import select
import socket
import time

import numpy as np
import tables

def ipv4_socket_address():
    # create an IPv4 socket address
    return ('127.0.0.1', random.randint(9000, 10000))

# process to receive an array using a socket
# for real use, this would require creating some protocol to specify the
# array's data type and shape
class SocketReceive(multiprocessing.Process):

    def __init__(self, socket_family, address, result_send, array_nbytes):
        super(SocketReceive, self).__init__()
        self.socket_family = socket_family
        self.address = address
        self.result_send = result_send
        self.array_nbytes = array_nbytes

    def run(self):
        # create the socket, listen for a connection and use select to block
        # until a connection is made
        sock = socket.socket(self.socket_family, socket.SOCK_STREAM)
        sock.bind(self.address)
        sock.listen(1)
        readable, _, _ = select.select([sock], [], [])
        # accept the connection and read the sent data into a bytearray
        connection = sock.accept()[0]
        recv_buffer = bytearray(self.array_nbytes)
        view = memoryview(recv_buffer)
        bytes_recv = 0
        while bytes_recv < self.array_nbytes:
            bytes_recv += connection.recv_into(view[bytes_recv:])
        # convert the bytearray into a NumPy array
        array = np.frombuffer(recv_buffer, dtype='i8')
        recv_timestamp = time.time()
        # perform an operation on the received array
        array += 1
        finish_timestamp = time.time()
        assert(np.all(array == 2))
        # send the timestamps back to the originating process
        self.result_send.send((recv_timestamp, finish_timestamp))
        connection.close()
        sock.close()

def read_and_send_socket(send_type, array_size, array_bytes, address_func,
                         socket_family):
    address = address_func()
    # start the receiving process and pause to allow it to start up
    result_recv, result_send = multiprocessing.Pipe(False)
    recv_process = SocketReceive(socket_family, address, result_send,
                                 array_bytes)
    recv_process.start()
    time.sleep(0.15)
    with tables.open_file('test.h5', 'r') as fobj:
        array = fobj.get_node('/', 'test')
        start_timestamp = time.time()
        # connect to the receiving process' socket
        sock = socket.socket(socket_family, socket.SOCK_STREAM)
        sock.connect(address)
        # read the array from the PyTables file and send its
        # data buffer to the receiving process
        output = array.read(0, array_size, 1)
        sock.send(output.data)
        assert(np.all(output + 1 == 2))
        # receive the timestamps from the other process
        recv_timestamp, finish_timestamp = result_recv.recv()
    sock.close()
    recv_process.join()

if __name__ == "__main__":
    read_and_send_socket('IPv4 socket', array_size, array_bytes,
                             ipv4_socket_address, socket.AF_INET)