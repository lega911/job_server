
import socket
from .utils import int_to_b3, b3_to_int, UnknownMethod, Error, WorkerException, recvall, byte_to_int

try:
    import queue
except ImportError:
    import Queue as queue


class WorkerHandler(object):
    """
    Example:

        rpc = WorkerHandler('localhost', 8011)
        rpc.add('ping', ping)
        rpc.add('echo', echo)
        rpc.serve()
        rpc.close()
    """
    def __init__(self, host, port):
        self.socket = None
        self.host = host
        self.port = port
        self.fn = {}

    def close(self):
        self.socket.close()
        self.socket = None

    def add(self, name, callback):
        self.fn[name.encode('utf8')] = callback

    def call(self, name, data):
        return self.fn[name](data)

    def recv_name_data(self, size):
        raw = recvall(self.socket, size)
        i = raw.find(b'\x00')
        if i < 0:
            raise Exception('Protocol error')
        return raw[:i], raw[i+1:]

    def serve(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        # 11, size_3b, name, 0, data
        fn = list(self.fn.keys())
        fn = sorted(fn)
        key = b','.join(fn)

        size = len(key)
        buf = b'\x0c' + int_to_b3(size) + key
        self.socket.sendall(buf)

        while self.socket:
            raw = recvall(self.socket, 4)
            flag = byte_to_int(raw[0])
            size = b3_to_int(raw[1:])
            if flag == 15:
                name, data = self.recv_name_data(size)
                result_code = b'\x10'
                try:
                    result = self.call(name, data)
                    assert isinstance(result, bytes), 'result is not bytes'
                except Exception as e:
                    result = str(e).encode('utf8')
                    result_code = b'\x13'

                assert len(result) < 0x1000000, 'Data is too big'
                raw = result_code + int_to_b3(len(result)) + result
                self.socket.sendall(raw)
            elif flag == 21:  # async
                name, data = self.recv_name_data(size)
                try:
                    self.call(name, data)
                except Exception as e:
                    pass
            else:
                raise Exception('Protocol error')


class ClientHandler(object):
    """
    Example:

        rpc = ClientHandler('localhost', 8010)
        rpc.call('echo', b'data')
        rpc.close()
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socks = queue.Queue()

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        return sock

    def close(self):
        while not self.socks.empty():
            self.socks.get_nowait().close()

    def call(self, method, data, async=False):
        # 11, size_3b, name, 0, data
        method = method.encode('utf8')
        size = len(method) + len(data) + 1
        assert size < 0x1000000, 'Data is too big'
        code = b'\x0d' if async else b'\x0b'
        buf = code + int_to_b3(size) + method + b'\x00' + data

        # get socket
        try:
            sock = self.socks.get_nowait()
        except queue.Empty:
            sock = self._connect()

        sock.sendall(buf)
        raw = recvall(sock, 4)
        code = byte_to_int(raw[0])
        if code in {16, 17, 18, 19}:
            size = b3_to_int(raw[1:])
            response = recvall(sock, size)
            self.socks.put_nowait(sock)
            if code == 16:
                return response
            elif code == 17:
                raise UnknownMethod(response.decode('utf8'))
            elif code == 18:
                raise Error(response.decode('utf8'))
            elif code == 19:
                raise WorkerException(response.decode('utf8'))
        elif code == 20:  # async task was accepted
            self.socks.put_nowait(sock)
        else:
            sock.close()
            raise Exception('Protocol error')
