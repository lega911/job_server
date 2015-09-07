
import socket
import struct


class UnknownMethod(Exception):
    pass


class Error(Exception):
    pass


class WorkerException(Exception):
    pass


class BaseHandler(object):
    def open(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def close(self):
        self.socket.close()

    def recvAll(self, size):
        left = size
        result = []
        while left:
            buf = self.socket.recv(left)
            if not buf:
                raise Exception('Socket closed')
            result.append(buf)
            left -= len(buf)
        return b''.join(result)


class WorkerHandler(BaseHandler):
    """
    Example:

        rpc = WorkerHandler()
        rpc.add('ping', ping)
        rpc.add('echo', echo)
        rpc.open('localhost', 8011)
        rpc.serve()
        rpc.close()
    """
    def __init__(self):
        self.fn = {}

    def add(self, name, callback):
        self.fn[name.encode('utf8')] = callback

    def call(self, name, data):
        return self.fn[name](data)

    def serve(self):
        # 11, size_2b, name, 0, data
        fn = list(self.fn.keys())
        fn = sorted(fn)
        key = b','.join(fn)

        size = len(key)
        buf = b'\x0c' + struct.pack('H', size) + key
        self.socket.sendall(buf)

        while True:
            raw = self.recvAll(3)
            raw = struct.unpack('BBB', raw)
            flag, size = raw[0], raw[1] + (raw[2] << 8)
            assert flag == 15
            raw = self.recvAll(size)
            assert len(raw) == size
            i = raw.find(b'\x00')
            assert i
            name = raw[:i]
            data = raw[i+1:]
            result_code = b'\x10'
            try:
                result = self.call(name, data)
            except Exception as e:
                result = str(e).encode('utf8')
                result_code = b'\x13'

            assert len(result) < 0x10000, 'Data is too big'
            raw = result_code + struct.pack('H', len(result)) + result
            self.socket.sendall(raw)


class ClientHandler(BaseHandler):
    def call(self, method, data):
        # 11, size_2b, name, 0, data
        size = len(method) + len(data) + 1
        assert size < 0x10000, 'Data is too big'
        buf = b'\x0b' + struct.pack('H', size) + method + b'\x00' + data
        self.socket.sendall(buf)
        raw = self.recvAll(3)
        code = raw[0]
        if code in {16, 17, 18, 19}:
            size = raw[1] + (raw[2] << 8)
            response = self.recvAll(size)
            if code == 16:
                return response
            elif code == 17:
                raise UnknownMethod(response.decode('utf8'))
            elif code == 18:
                raise Error(response.decode('utf8'))
            elif code == 19:
                raise WorkerException(response.decode('utf8'))
        else:
            raise Exception('Error block code')
