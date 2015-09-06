package main

import (
    "fmt"
    "net"
    "os"
    "sync"
    "strings"
)

const (
    WORKER_ADDRESS = "localhost:8011"
)


var g_chainIndex uint16
var g_chainIndexMutex sync.Mutex

var g_chainByKey map[string]uint16
var g_chainByFn map[string]uint16
var g_connByChainIndex map[uint16] chan net.Conn

func initVariables() {
    g_chainIndex = 1
    g_chainByKey = make(map[string]uint16)
    g_chainByFn = make(map[string]uint16)
    g_connByChainIndex = make(map[uint16] chan net.Conn)
    g_chainIndexMutex = sync.Mutex{}
}

func workerDispatcher() {
    initVariables()
    fmt.Println("Worker dispatcher listening on " + WORKER_ADDRESS)
    l, err := net.Listen("tcp", WORKER_ADDRESS)
    if err != nil {
        fmt.Println("Error listening:", err.Error())
        os.Exit(1)
    }
    // Close the listener when the application closes.
    defer l.Close()
    for {
        // Listen for an incoming connection.
        conn, err := l.Accept()
        if err != nil {
            fmt.Println("Error accepting: ", err.Error())
            os.Exit(1)
        }
        // Handle connections in a new goroutine.
        go workerHandler(conn)
    }
}

// Handles incoming requests.
func workerHandler(conn net.Conn) {
    flag, data := tcpReadBlock(conn)

    if flag == 12 {
        keyLine := string(data)
        fmt.Println("keyLine", keyLine)

        chainIndex := getChainIndex(keyLine)

        // reg methods  
        keys := strings.Split(keyLine, ",")
        for _, key := range keys {
            g_chainByFn[key] = chainIndex
        }

        g_connByChainIndex[chainIndex] <- conn
    } else {
        conn.Close()        
        fmt.Println("Wrong command")
    }
}


func getChainIndex(key string) (uint16) {
    index := g_chainByKey[key]
    if index == 0 {
        g_chainIndexMutex.Lock()
        index = g_chainByKey[key]  // could be changed before lock
        if index == 0 {
            index = g_chainIndex
            g_chainIndex += 1
            g_chainByKey[key] = index
            g_connByChainIndex[index] = make(chan net.Conn)
            fmt.Println("new worker chain", index)
        }
        g_chainIndexMutex.Unlock()
    }
    return index
}
