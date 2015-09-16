
import asyncio
from jclient.async import WorkerAsyncHandler


async def ping(raw):
    print('ping', raw)
    await asyncio.sleep(1)
    return b'pong'


def echo(raw):
    return raw


async def worker(loop):
    rpc = WorkerAsyncHandler('localhost', 8011, loop=loop)
    rpc.add('ping', ping)
    rpc.add('echo', echo)
    await rpc.serve()


loop = asyncio.get_event_loop()
loop.run_until_complete(worker(loop))
loop.close()
