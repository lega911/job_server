package main

import (
    "fmt"
    "time"
)

var g_counter chan int64

func getTick() (int64) {
    return time.Now().UnixNano() / int64(time.Millisecond)
}

func runCounter() {
    total := int64(0)
    g_counter = make(chan int64)
    start := getTick()
    var now int64
    for v := range g_counter {
        total += v
        now = getTick()

        duration := now - start
        if duration > 1000 {
            fmt.Println("Counter: ", 1000 * total / duration)
            start = now
            total = 0
        }

    }
}
