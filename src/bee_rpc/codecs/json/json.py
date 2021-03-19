import json
from typing import List

from bee_util.data.option import Options, Option
from bee_util.data.map import Map
from bee_util.errors.error import CodedError
from bee_rpc.codec import CodecBuilder, Request as _Request, RequestHead as _RequestHead, ResponseHead as _ResponseHead, \
    Response as _Response, Result as _Result, register_codec, IClientCodec, Stream, IServerCodec


class Request():
    name = "request"
    def __init__(self):
        self.head = _RequestHead
        self.args: List[bytes] = []

    def reset(self):
        self.head.id = 0
        self.head.service = ""
        self.head.method = ""
        if self.head.labels != None:
            self.head.labels = self.head.labels[:0]

        if self.args != None:
            self.args = self.args[:0]

class Result():
    name = "result"
    def __init__(self):
        self.value: bytes = None
        self.error: CodedError = None


class Response():
    name = "response"

    def __init__(self):
        self.head: _ResponseHead = None
        self.result: Result = None

    def reset(self):
        self.head = 0
        self.result.value = None
        self.result.error = None

class ClientCodec(IClientCodec):
    """
    客户端编解码
    """

    def __init__(self, s: Stream, req=Request(), resp: Response = None):
        self.s = s
        self.req: Request = req
        self.resp: Response = resp

    def stream(self) -> Stream:
        return self.s

    def encode(self, req: _Request):

        json_str = json.dumps(req, default=lambda o: o.__dict__, sort_keys=True)
        print(json_str)
        data = json_str.encode(encoding="utf-8")
        self._write(data)

    def _write(self, data: bytes):
        # wtire data's length, occupy 4 bytes

        self.s.write(len(data).to_bytes(4, byteorder='little'))
        # write data
        self.s.write(data)
        self.s.flush()

    def discard_result(self):
        return None

    def decode_head(self, head: _ResponseHead):
        length_bytes = self.s.read(4);
        length = int.from_bytes(length_bytes, byteorder="little")

        data = self.s.read(length)
        # self.resp = json.loads(bytes(data).decode(encoding="utf-8"), cls=Response)
        # self.resp = json.loads(bytes(data).decode(encoding="utf-8"), cls=Response)
        result = json.loads(bytes(data).decode(encoding="utf-8"))
        print(result)
        _head = _ResponseHead(id=result["head"]["id"])
        _result = _Result(value=result["result"]["value"], error=result["result"]["error"])
        self.resp.head = _head
        self.resp.result = _result

        head.id = self.resp.head.id


    def decode_result(self, result: _Result):
        if self.resp.result.value != None:
            result.error = None
            result.value = self.resp.result.value
        else:
            result.error = self.resp.result.error


class ServerCodec(IServerCodec):
    """
    服务端编解码
    """

    def __init__(self, s: Stream, req: Request = None, resp: Response = None):
        self.s = s
        self.req = req
        self.resp = resp

    def stream(self) -> Stream:
        return self.s

    def encode(self, resp: _Response):
        self.resp.head = resp.head

        result = Result()
        if resp.result.error == None:
            if resp.result.value != None:
                result.value = resp.result.value
        else:
            result.error = resp.result.error
        self.resp.result = result
        json_str = json.dumps(self.resp, default=lambda o: o.__dict__, sort_keys=True)
        # print(json_str)
        data = json_str.encode(encoding="utf-8")
        self._write(data)

    def _write(self, data: bytes):
        # wtire data's length, occupy 4 bytes
        self.s.write(len(data).to_bytes(4, byteorder='little'))
        # write data
        self.s.write(data)
        self.s.flush()

    def decode_head(self, head: _RequestHead):
        length_bytes = self.s.read(4);
        length = int.from_bytes(length_bytes, byteorder="little")
        if length ==0:
            return
        data = self.s.read(length)
        # print(data)
        result = json.loads(data)
        self.req.args = result["args"]
        _head = _RequestHead()
        _head.id = result["head"]["id"]
        _head.service = result["head"]["service"]
        _head.method = result["head"]["method"]
        self.req.head = _head

        head.id = self.req.head.id
        head.service = self.req.head.service
        head.method = self.req.head.method
        if self.req.head.labels:
            opts = Options()
            for v in self.req.head.labels:
                opts.append(Option(name=v.name, value=v.value))
            head.labels = opts
        if head.id != None and head.id > 0:
            print("%s, %s.%s(%s), labels(%s)" % (head.id, head.service, head.method, "", head.labels))

    def decode_args(self, args: List[object]):
        if self.req.args != None:
            for i, v in enumerate(self.req.args):
                args.insert(i, v)

    def discard_args(self):
        return None


class Builder(CodecBuilder):

    name="json"

    def new_client_codec(self, s: Stream, opts: Map) -> ClientCodec:
        return ClientCodec(s=s, req=Request(), resp=Response())

    def new_server_codec(self, s: Stream, opts: Map) -> ServerCodec:
        return ServerCodec(s=s, req=Request(), resp=Response())


def init():
    register_codec("json", Builder())