
import socket
import queue
import asyncio
import inspect


class UnknownMethod(Exception):
    pass


class Error(Exception):
    pass


class WorkerException(Exception):
    pass


def int_to_b3(i):
    return bytes([i & 0xff, (i & 0xff00) >> 8, (i & 0xff0000) >> 16])


def b3_to_int(b):
    return b[0] + (b[1] << 8) + (b[2] << 16)


def recvall(sock, size):
    left = size
    result = []
    while left:
        buf = sock.recv(left)
        if not buf:
            raise Exception('Socket closed')
        result.append(buf)
        left -= len(buf)
    return b''.join(result)


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
            flag = raw[0]
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

    def call(self, method, data, *, async=False):
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
        code = raw[0]
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


class ClientAsyncHandler(object):
    """
    Example:

        @asyncio.coroutine
        def run(loop):
            rpc = jclient.ClientAsyncHandler('localhost', 8010, loop=loop)

            result = yield from rpc.call('ping', b'data')
            print(result)

            rpc.close()


        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(loop))
        loop.close()
    """
    def __init__(self, host, port, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.host = host
        self.port = port
        self.socks = asyncio.Queue()

    @asyncio.coroutine
    def call(self, method, data, *, async=False):
        method = method.encode('utf8')
        size = len(method) + len(data) + 1
        assert size < 0x1000000, 'Data is too big'
        code = b'\x0d' if async else b'\x0b'
        buf = code + int_to_b3(size) + method + b'\x00' + data

        try:
            reader, writer = self.socks.get_nowait()
        except asyncio.QueueEmpty:
            reader, writer = yield from asyncio.open_connection(self.host, self.port, loop=self.loop)

        writer.write(buf)

        raw = yield from reader.read(4)
        if not raw:
            # socket was closed
            raise Exception('Socket closed')
        code = raw[0]
        if code in {16, 17, 18, 19}:
            size = b3_to_int(raw[1:])
            response = yield from reader.read(size)
            assert len(response) == size
            self.socks.put_nowait((reader, writer))
            if code == 16:
                return response
            elif code == 17:
                raise UnknownMethod(response.decode('utf8'))
            elif code == 18:
                raise Error(response.decode('utf8'))
            elif code == 19:
                raise WorkerException(response.decode('utf8'))
        elif code == 20:  # async task was accepted
            self.socks.put_nowait((reader, writer))
        else:
            self.close()
            raise Exception('Protocol error')

    def close(self):
        while not self.socks.empty():
            reader, writer = self.socks.get_nowait()
            writer.close()


class WorkerAsyncHandler(object):
    """
    Example:
        @asyncio.coroutine
        def worker(loop):
            rpc = jclient.WorkerAsyncHandler('localhost', 8011, loop=loop)
            rpc.add('ping', ping)
            rpc.add('echo', echo)
            yield from rpc.serve()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(loop))
        loop.close()
    """
    def __init__(self, host, port, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.host = host
        self.port = port
        self.fn = {}
        self.writer = None
        self.reader = None

    def close(self):
        self.writer.close()
        self.writer = None
        self.reader = None

    def add(self, name, callback):
        self.fn[name.encode('utf8')] = callback

    @asyncio.coroutine
    def call(self, name, data):
        result = self.fn[name](data)
        if inspect.isgenerator(result) or isinstance(result, asyncio.Future):
            result = yield from result
        return result

    @asyncio.coroutine
    def recv_name_data(self, size):
        raw = yield from self.reader.read(size)
        assert len(raw) == size
        i = raw.find(b'\x00')
        if i < 0:
            raise Exception('Protocol error')
        return raw[:i], raw[i+1:]

    @asyncio.coroutine
    def serve(self):
        self.reader, self.writer = reader, writer = yield from asyncio.open_connection(self.host, self.port, loop=self.loop)

        # 11, size_3b, name, 0, data
        fn = list(self.fn.keys())
        fn = sorted(fn)
        key = b','.join(fn)

        size = len(key)
        buf = b'\x0c' + int_to_b3(size) + key
        writer.write(buf)

        while self.writer:
            raw = yield from reader.read(4)
            if not raw:
                # socket was closed
                raise Exception('Socket closed')

            flag = raw[0]
            size = b3_to_int(raw[1:])
            if flag == 15:
                name, data = yield from self.recv_name_data(size)
                result_code = b'\x10'
                try:
                    result = yield from self.call(name, data)
                    assert isinstance(result, bytes), 'result is not bytes'
                except Exception as e:
                    result = str(e).encode('utf8')
                    result_code = b'\x13'

                assert len(result) < 0x1000000, 'Data is too big'
                raw = result_code + int_to_b3(len(result)) + result
                writer.write(raw)
            elif flag == 21:  # async
                name, data = yield from self.recv_name_data(size)
                try:
                    yield from self.call(name, data)
                except Exception as e:
                    print(e)
            else:
                raise Exception('Protocol error')
