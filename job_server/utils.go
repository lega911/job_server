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
        body = body[:lenRead]
        // need read more
        sizeLeft := size - lenRead

        for sizeLeft > 0 {
            buf := make([]byte, sizeLeft)
            lenRead, err = conn.Read(buf)

            if err != nil {
                if (err == io.EOF) && (lenRead != sizeLeft) {
                    return 0, nil
                } else {
                    fmt.Println("Read error: ", err.Error())
                    return 0, nil
                }
            }
            body = append(body, buf[:lenRead]...)
            sizeLeft = sizeLeft - lenRead
        }
    }

    // double check
    if len(body) != size {
        fmt.Println(len(body), size)
        panic("Error read body")
    }

    return head[0], body
}


func tcpWriteBlock(conn net.Conn, flag byte, data []byte) (int) {
    size := len(data)
    head := []byte{flag, byte(size & 0xff), byte(size >> 8)}
    lenWrote, err := conn.Write(head)
    if err != nil {
        fmt.Println("Write head error: ", err.Error())
        return 1
    }
    if lenWrote != 3 {
        fmt.Println("Write head error")
        return 2
    }
    sent := 0
    for sent < size {
        lenWrote, err = conn.Write(data[sent:])
        if err != nil {
            fmt.Println("Write error: ", err.Error())
            return 3
        }
        sent += lenWrote
    }
    return 0
}


func parseArgs() {
    WORKER_ADDRESS = "localhost:8011"
    CLIENT_ADDRESS = "localhost:8010"
    LOGGING = false
    COUNTER = false
    for _, k := range os.Args[1:] {
        if WORKER_ADDRESS == "" {
            WORKER_ADDRESS = k
            continue
        }
        if CLIENT_ADDRESS == "" {
            CLIENT_ADDRESS = k
            continue
        }

        if k == "-log" {
            LOGGING = true
            continue
        }
        if k == "-counter" {
            COUNTER = true
            continue
        }
        if k == "-worker" {
            WORKER_ADDRESS = ""
            continue
        }
        if k == "-client" {
            CLIENT_ADDRESS = ""
            continue
        }
    }
}
