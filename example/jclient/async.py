
import asyncio
import inspect
from .utils import int_to_b3, b3_to_int, UnknownMethod, Error, WorkerException


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
        if inspect.isgenerator(result) or inspect.isawaitable(result) or isinstance(result, asyncio.Future):
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
