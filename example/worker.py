
import jclient


def ping(data):
    return b'pong'


def echo(data):
    return data

rpc = jclient.WorkerHandler('localhost', 8011)
rpc.add('ping', ping)
rpc.add('echo', echo)
rpc.serve()
rpc.close()
