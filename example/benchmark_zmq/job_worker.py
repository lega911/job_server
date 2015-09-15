
import jclient
import msgpack


class Worker(jclient.WorkerHandler):
    """
        msg-pack wrapper
    """
    def call(self, name, data):
        result = super().call(name, msgpack.unpackb(data, encoding='utf-8'))
        return msgpack.packb(result)


def ping(data):
    assert data == 'ping'
    return 'pong'


rpc = Worker('localhost', 8011)
rpc.add('ping', ping)
rpc.serve()
