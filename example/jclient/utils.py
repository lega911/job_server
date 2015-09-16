
import sys


class UnknownMethod(Exception):
    pass


class Error(Exception):
    pass


class WorkerException(Exception):
    pass


if sys.version_info.major >= 3:
    def int_to_b3(i):
        return bytes([i & 0xff, (i & 0xff00) >> 8, (i & 0xff0000) >> 16])

    def b3_to_int(b):
        return b[0] + (b[1] << 8) + (b[2] << 16)

    def byte_to_int(b):
        return b
else:
    def int_to_b3(i):
        return b''.join(map(chr, [i & 0xff, (i & 0xff00) >> 8, (i & 0xff0000) >> 16]))

    def b3_to_int(b):
        return ord(b[0]) + (ord(b[1]) << 8) + (ord(b[2]) << 16)

    def byte_to_int(b):
        return ord(b)


def recvall(sock, size):
    left = size
    result = []
    while left:
        buf = sock.recv(left)
        if not buf:
            raise Exception('Socket closed')
        result.append(buf)
        left -= len(buf)
    return b''.join(result)
