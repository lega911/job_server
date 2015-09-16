
import asyncio
from jclient.async import WorkerAsyncHandler


@asyncio.coroutine
def ping(raw):
    yield from asyncio.sleep(1)
    return b'pong'


def echo(raw):
    return raw


@asyncio.coroutine
def worker(loop):
    rpc = WorkerAsyncHandler('localhost', 8011, loop=loop)
    rpc.add('ping', ping)
    rpc.add('echo', echo)
    yield from rpc.serve()


loop = asyncio.get_event_loop()
loop.run_until_complete(worker(loop))
loop.close()
