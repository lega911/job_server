
import asyncio
import aiozmq.rpc
import time


@asyncio.coroutine
def go(client, stat):
    while True:
        ret = yield from client.call.ping('ping')
        assert ret == 'pong'
        stat.count += 1

        if stat.count >= 10000:
            duration = time.time() - stat.start
            print(stat.count / duration)
            stat.start = time.time()
            stat.count = 0


@asyncio.coroutine
def connect():
    class stat:
        count = 0
        start = time.time()

    client = yield from aiozmq.rpc.connect_rpc(connect='tcp://127.0.0.1:5555')

    asyncio.async(go(client, stat))
    #asyncio.async(go(client, stat))

asyncio.async(connect())
asyncio.get_event_loop().run_forever()
