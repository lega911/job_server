
import jclient
import time


def benchmark(rpc):
    while True:
        result = rpc.call(b'ping', b'data')
        #print(result)
        if result != b'pong':
            print('Wrong result', result)


def send_one(rpc):
    data = b'0123456789' * 6400  # 64k
    result = rpc.call(b'echo', data)
    print(len(result))
    assert data == result


rpc = jclient.ClientHandler()
rpc.open('localhost', 8010)

benchmark(rpc)
#send_one(rpc)

rpc.close()
