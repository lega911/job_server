package main

import (
    "fmt"
)

var LOGGING bool
var COUNTER bool

func main() {
    parseArgs()
    if LOGGING {        
        fmt.Println("Start")
    }
    if COUNTER {
        go runCounter()
    }
    go clientDispatcher()
    workerDispatcher()
}
