### job_server on Go + python client

### Compile
``` bash
go build -o jserver job_server/*.go
```

### Run
``` bash
> jserver
```

#### Arguments

* -log
* -couter
* -client localhost:8010
* -worker localhost:8011

### Example of python worker
``` python
import jclient

def echo(data):
    return data

rpc = jclient.WorkerHandler()
rpc.add('echo', echo)  #  attach a method
rpc.open('localhost', 8011)
rpc.serve()
rpc.close()
```

### Example of python client
``` python
import jclient

rpc = jclient.ClientHandler()
rpc.open('localhost', 8010)
result = rpc.call(b'echo', b'data')  # call a method
rpc.close()
```