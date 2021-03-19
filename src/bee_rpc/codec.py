from typing import List

from bee_util.data.option import Options
from bee_util.data.map import Map
from bee_util.data import const

const.codecs = Map()


class ReadPeeker():
    def read(self, p: bytes) -> int:
        pass

    def peek(self, n: int) -> bytes:
        pass


class Stream(ReadPeeker):

    def id(self) -> str:
        pass

    def reader(self):
        pass

    def peek(self, n: int) -> bytes:
        pass

    def read(self, n: int) -> bytes:
        pass

    def read_bytes(self, separator=b'\n') -> bytes:
        pass

    def read_str(self, separator=b'\n') -> str:
        pass

    def writer(self):
        pass

    def write(self, p: bytes) -> int:
        pass

    def write_str(self, s:str):
        pass

    def flush(self):
        pass


class RequestHead():
    def __init__(self,id: int = None, service: str = None, method: str = None, labels: Options = None, assets: Options = None):
        self.id = id
        self.service = service
        self.method = method
        self.labels = labels
        self.assets = assets

class Request():

    def __init__(self, head: RequestHead = None, args: List[object] = []):
        self.head = head
        self.args = args


class ResponseHead():

    def __init__(self, id: int = None, assets: Options = None):
        self.id = id
        self.assets = assets



class Result():

    def __init__(self, value: object = None, error = None):
        self.value = value
        self.error = error


class Response():

    def __init__(self, head: ResponseHead = None, result: Result = None):
        self.head = head
        self.result = result


class IClientCodec():

    def stream(self) -> Stream:
        pass

    def encode(self, req: Request):
        pass

    def decode_head(self, head: ResponseHead):
        pass

    def decode_result(self, result: Result):
        pass

    def discard_result(self):
        pass


class IServerCodec():

    def stream(self) -> Stream:
        pass

    def encode(self, resp: Response):
        pass

    def decode_head(self, head: RequestHead):
        pass

    def decode_args(self, args: []):
        pass

    def discard_args(self):
        pass


class CodecBuilder():

    def new_client_codec(self, s: Stream, opts: Map) -> IClientCodec:
        pass

    def new_server_codec(self, s: Stream, opts: Map) -> IServerCodec:
        pass


def register_codec(name: str, cb: CodecBuilder):
    const.codecs.set(name, cb)

def get_codec(name: str) -> CodecBuilder:
    return const.codecs.get(name)


class Macther():

    def match(self, ReadPeeker) -> bool:
        pass

class Any(Macther):
    def match(self, ReadPeeker) -> bool:
        return True