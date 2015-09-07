package main

import (
    "fmt"
    "net"
    "os"
    //"strings"
    "bytes"
)

var CLIENT_ADDRESS string

func clientDispatcher() {
    fmt.Println("Client dispatcher listening on " + CLIENT_ADDRESS)
    l, err := net.Listen("tcp", CLIENT_ADDRESS)
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
        go clientHandler(conn)
    }
}

func getChainIndexByRequest(conn net.Conn, data []byte) (uint16, int) {
    // chainIndex, error
    i := bytes.IndexByte(data, 0)
    if i < 1 {
        fmt.Println("Wrong block")
        return 0, 1
    }
    key := string(data[:i])
    chainIndex := g_chainByFn[key]
    if LOGGING {
        fmt.Println("Method: ", key, chainIndex)
    }    
    if chainIndex < 1 {
        fmt.Println("Unknown method ", key)
        if tcpWriteBlock(conn, 17, []byte(key)) != 0 {
            return 0, 1
        }
        return 0, 2
    }
    return chainIndex, 0
}

// Handles incoming requests.
func clientHandler(conn net.Conn) {
    defer conn.Close()
    fmt.Println("New client")
    counter := int64(0)

    for {
        if COUNTER {
            counter += 1
            if counter > 1000 {
                g_counter <- counter
                counter = 0
            }
        }
        
        flag, data := tcpReadBlock(conn)
        if flag == 0 {
            fmt.Println("Client disconnected")
            return
        } else if flag == 11 {
            chainIndex, err := getChainIndexByRequest(conn, data)
            if err != 0 {
                if err == 1 {
                    return
                } else if err == 2 {
                    continue
                }                
            }

            wait_worker:
            if LOGGING {
                fmt.Println("waiting for a worker")
            }
            worker := <- g_connByChainIndex[chainIndex]
            if LOGGING {
                fmt.Println("worker accepted")
            }
            if tcpWriteBlock(worker, 15, data) != 0 {
                fmt.Println("Error write to worker")
                goto wait_worker
            }

            rFlag, response := tcpReadBlock(worker)
            if rFlag == 0 {
                // net error
                fmt.Println("Error read from worker")
                if tcpWriteBlock(conn, 18, response) != 0 {
                    return
                }
                continue
            }

            // push worker back
            go func(c net.Conn) {
                g_connByChainIndex[chainIndex] <- c
                if LOGGING {
                    fmt.Println("worker released")
                }
            }(worker)

            if (rFlag != 16) && (rFlag != 19) {
                fmt.Println("Wrong response")
                if tcpWriteBlock(conn, 18, []byte("Wrong response")) != 0 {
                    return
                }
                continue
            }

            if tcpWriteBlock(conn, rFlag, response) != 0 {
                return
            }
        } else if flag == 13 {
            chainIndex, err := getChainIndexByRequest(conn, data)
            if err != 0 {
                if err == 1 {
                    return
                } else if err == 2 {
                    continue
                }                
            }

            go func(chainIndex uint16, data []byte) {
                wait_worker_async:
                worker := <- g_connByChainIndex[chainIndex]
                if LOGGING {
                    fmt.Println("worker accepted")
                }
                if tcpWriteBlock(worker, 21, data) != 0 {
                    fmt.Println("Error write to worker")
                    goto wait_worker_async
                }
                g_connByChainIndex[chainIndex] <- worker
                if LOGGING {
                    fmt.Println("worker released")
                }                
            }(chainIndex, data)

            if tcpWriteBlock(conn, 20, nil) != 0 {
                return
            }            
        } else {
            fmt.Println("Error request from client")
            return
        }
    }
}
