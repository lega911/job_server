
import asyncio
import aiozmq.rpc


class ServerHandler(aiozmq.rpc.AttrHandler):
    @aiozmq.rpc.method
    def ping(self, data):
        return 'pong'


@asyncio.coroutine
def go():
    yield from aiozmq.rpc.serve_rpc(ServerHandler(), bind='tcp://127.0.0.1:5555')

asyncio.async(go())
asyncio.get_event_loop().run_forever()
