
import jclient
import time


def benchmark(rpc):
    while True:
        result = rpc.call('ping', b'data')
        if result != b'pong':
            print('Wrong result', result)


def benchmark_async(rpc):
    i = 0
    while True:
        rpc.call('ping', str(i).encode('utf8'), async=True)
        i += 1


def send_one(rpc):
    data = b'0123456789' * 12800  # 128k
    result = rpc.call('echo', data)
    print(len(result))
    assert data == result


rpc = jclient.ClientHandler('localhost', 8010)
try:
    benchmark(rpc)
    #send_one(rpc)
    #benchmark_async(rpc)
finally:
    rpc.close()
