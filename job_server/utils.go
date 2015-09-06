package main

import (
    "fmt"
    "net"
    "io"
    "os"
)

func tcpReadBlock(conn net.Conn) (byte, []byte) {
    // read head
    head := make([]byte, 3)
    lenRead, err := conn.Read(head)
    if err == io.EOF {
        return 0, nil
    }
    if err != nil {
        fmt.Println("Read error: ", err.Error())
        return 0, nil
    }
    if lenRead != 3 {
        panic("Error read head")
    }
    size := int(head[1]) + int(head[2]) << 8

    // read body
    body := make([]byte, size)
    lenRead, err = conn.Read(body)
    if err != nil {
        panic(err.Error())
    }
    if lenRead != size {
        panic("Error read body")
    }

    return head[0], body
}


func tcpWriteBlock(conn net.Conn, flag byte, data []byte) {
    size := len(data)
    head := []byte{flag, byte(size & 0xff), byte(size >> 8)}
    conn.Write(head)
    conn.Write(data)
}


func parseArgs() {
    LOGGING = false
    COUNTER = false
    for _, k := range os.Args[1:] {
        if k == "-log" {
            LOGGING = true
        }
        if k == "-counter" {
            COUNTER = true
        }
    }
}
