
import socket
import struct

class RPC:
    def open(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def close(self):
        self.socket.close()

    def call(self, method, data):
        # 11, size_2b, name, 0, data
        size = len(method) + len(data) + 1
        buf = b'\x0b' + struct.pack('H', size) + method + b'\x00' + data
        self.socket.sendall(buf)
        #print('sent')
        raw = self.socket.recv(3)
        assert raw[0] == 16
        size = raw[1] + raw[2] << 8
        response = self.socket.recv(size)
        #print(response)
        return response


rpc = RPC()
rpc.open('localhost', 8010)

while True:
    result = rpc.call(b'ping', b'data')
    #print(result)
    if result != b'pong':
        print('Wrong result', result)

rpc.close()
