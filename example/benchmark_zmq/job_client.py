
import asyncio
import jclient
import msgpack
import time


class Client(jclient.ClientAsyncHandler):
    """
        msg-pack wrapper
    """
    @asyncio.coroutine
    def call(self, method, data, *, async=False):
        result = yield from super().call(method, msgpack.packb(data), async=async)
        return msgpack.unpackb(result, encoding='utf-8')


@asyncio.coroutine
def go(client, stat):
    while True:
        ret = yield from client.call('ping', 'ping')
        assert ret == 'pong'
        stat.count += 1

        if stat.count >= 10000:
            duration = time.time() - stat.start
            print(stat.count / duration)
            stat.start = time.time()
            stat.count = 0


@asyncio.coroutine
def connect(loop):
    class stat:
        count = 0
        start = time.time()

    client = Client('localhost', 8010, loop=loop)

    asyncio.async(go(client, stat))
    #asyncio.async(go(client, stat))

loop = asyncio.get_event_loop()
asyncio.async(connect(loop))
loop.run_forever()
