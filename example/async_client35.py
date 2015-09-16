
import asyncio
from jclient.async import ClientAsyncHandler


async def run(loop):
    rpc = ClientAsyncHandler('localhost', 8010, loop=loop)

    result = await rpc.call('ping', b'data')
    print(result)

    rpc.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
loop.close()
