
import jclient


def ping(data):
    return b'pong'


def echo(data):
    return data

rpc = jclient.WorkerHandler()
rpc.add('ping', ping)
rpc.add('echo', echo)
rpc.open('localhost', 8011)
rpc.serve()
rpc.close()
