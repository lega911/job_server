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

rpc = jclient.WorkerHandler('localhost', 8011)
rpc.add('echo', echo)  #  attach a method
rpc.serve()
rpc.close()
```

### Example of python client
``` python
import jclient

rpc = jclient.ClientHandler('localhost', 8010)
result = rpc.call('echo', b'data')  # call a method
rpc.close()
```

### Example of python asyncio client
``` python
import asyncio
import jclient

@asyncio.coroutine
def run(loop):
    rpc = jclient.ClientAsyncHandler('localhost', 8010, loop=loop)

    result = yield from rpc.call('ping', b'data')
    print(result)

    rpc.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
loop.close()
```

### License
[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2015 Oleg Nechaev <lega911@gmail.com>
