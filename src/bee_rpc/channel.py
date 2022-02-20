from gevent import socket

from bee_util.data.guid import Guid
from bee_rpc.codec import Stream


class Channel(Stream):

    def __init__(self, id: str = None, sock=None):
        self._id = id
        self._r: socket = sock
        self._w: socket = sock
        #u 用户
        self.u = None

    def id(self) -> str:
        return self._id

    def reader(self) -> socket:
        return self._r

    def writer(self) -> socket:
        return self._w

    def peek(self, n: int) -> bytes:
        """
        瞄一眼
        :param n:
        :return:
        """
        pass


    def read(self, n: int) -> bytes:
        if self._r.closed:
            raise IOError("socket关闭")
        return self._r.recv(n)

    def read_bytes(self, separator=b'\n') -> bytes:
        if self._r.closed:
            raise IOError("socket关闭")
        ba = bytearray()
        while True:
            b = self._r.recv(1)
            if(b==separator):
                break
            ba.append(int.from_bytes(b, byteorder="little"))
        return bytes(ba)

    def read_str(self, separator=b'\n') -> str:
        data = self.read_bytes(separator)
        if not data:
            return data.decode(encoding="utf-8")
        return None

    def write(self, p: bytes) -> int:
        if self._w.closed:
            raise IOError("socket关闭")
        length = len(p)
        if length > 0:
            self._w.send(p)
            return length
        return 0

    def write_str(self, s:str):
        if self._w.closed:
            raise IOError("socket关闭")
        if s != None:
            data = s.encode(encoding="utf-8")
            self._w.send(data)
            return len(data)
        return 0

    def flush(self):
        # self._w.close()
        # pass
        self._w.sendall("".encode(encoding="utf-8"))

def new_channel(sock) -> Channel:
    return Channel(id=Guid().string(), sock=sock)
