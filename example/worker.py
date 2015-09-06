
import socket
import struct

class RPC:
    def __init__(self):
        self.fn = {}

    def open(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def close(self):
        self.socket.close()

    def add(self, name, callback):
        self.fn[name.encode('utf8')] = callback

    def serve(self):
        # 11, size_2b, name, 0, data
        fn = list(self.fn.keys())
        fn = sorted(fn)
        key = b','.join(fn)

        size = len(key)
        buf = b'\x0c' + struct.pack('H', size) + key
        self.socket.sendall(buf)

        while True:
            raw = self.socket.recv(3)
            #print('request', raw)
            raw = struct.unpack('BBB', raw)
            flag, size = raw[0], raw[1] + (raw[2] << 8)
            assert flag == 15
            raw = self.socket.recv(size)
            #print('Size', size, len(raw))
            assert len(raw) == size
            i = raw.find(b'\x00')
            assert i
            name = raw[:i]
            data = raw[i+1:]
            #print('R: ', name, data)

            result = self.fn[name](data)

            raw = b'\x10' + struct.pack('H', len(result)) + result
            self.socket.sendall(raw)

def ping(data):
    return b'pong'

def echo(data):
    return data

rpc = RPC()
rpc.add('ping', ping)
rpc.add('echo', echo)
rpc.open('localhost', 8011)
rpc.serve()
rpc.close()
