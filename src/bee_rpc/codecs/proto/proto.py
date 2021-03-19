import pickle

from typing import List

from bee_util.data.option import Options, Option
from bee_util.data.map import Map
from bee_util.errors.error import CodedError
from bee_rpc.codec import Stream, IClientCodec, IServerCodec, CodecBuilder, Request as _Request, RequestHead as _RequestHead, ResponseHead as _ResponseHead, \
    Response as _Response, Result as _Result, register_codec
from bee_util.data import const

# 缺省最大值
from bee_rpc.codecs.proto.msg_pb2 import Label, Response, Request

const.default_max_message_size = 2 << 20


def reset_req(req: Request):
    if req.args != None:
        req.args = req.args[:0]
    if req.labels != None:
        req.labels = req.labels[:0]


def reset_resp(resp: Response):
    resp.result = None
    resp.error = None


class ClientCodec(IClientCodec):
    """
    客户端编解码
    """

    def __init__(self, s: Stream, req: Request = None, resp: Response = None, max_msg_size=0):
        self.s = s
        self.req = req
        self.resp = resp
        self.max_msg_size = max_msg_size

    def stream(self) -> Stream:
        return self.s

    def encode(self, req: _Request):
        self.req.id = req.head.id
        self.req.service = req.head.service
        self.req.method = req.head.method

        if len(req.args) > 0:
            for v in req.args:
                # convert v to bytes, v is object
                self.req.args.append(pickle.dumps(v))

        if len(req.head.labels) > 0:
            for v in req.head.labels:
                self.req.labels.append(Label(name=v.name, value=v.value))

        self._write(self.req.SerializeToString())

    def _write(self, data: bytes):
        # wtire data's length, occupy 4 bytes
        self.s.write(len(data).to_bytes(4, byteorder='little'))
        # write data
        self.s.write(data)
        self.s.flush()

    def decode_head(self, head: _ResponseHead):
        length_bytes = self.s.read(4);
        length = int.from_bytes(length_bytes, byteorder="little")
        if length > self.max_msg_size:
            raise BaseException("message too big: %s" % length)

        data = self.s.read(length)
        self.resp.ParseFromString(data)
        head.id = self.resp.id

    def decode_result(self, result: _Result):
        if self.resp.result != None:
            result.error = None
            if len(self.resp.result) > 0:
                result.value = pickle.loads(self.resp.result)
            else:
                result.value = None
        else:
            result.error = CodedError(self.resp.error)

    def discard_result(self):
        return None


class ServerCodec(IServerCodec):
    """
    服务端编解码
    """

    def __init__(self, s: Stream, req: Request = None, resp: Response = None, max_msg_size=0):
        self.s = s
        self.req = req
        self.resp = resp
        self.max_msg_size = max_msg_size

    def stream(self) -> Stream:
        return self.s

    def encode(self, resp: _Response):
        self.resp.id = resp.head.id

        if resp.result.error == None:
            if resp.result.value != None:
                self.resp.result = pickle.dumps(resp.result.value)
        else:
            self.resp.result = None
            self.resp.error = resp.result.error

        self._write(self.resp.SerializeToString())

    def _write(self, data: bytes):
        # wtire data's length, occupy 4 bytes
        self.s.write(len(data).to_bytes(4, byteorder='little'))
        # write data
        self.s.write(data)
        self.s.flush()

    def decode_head(self, head: _RequestHead):
        length_bytes = self.s.read(4);
        length = int.from_bytes(length_bytes, byteorder="little")
        if length > self.max_msg_size:
            raise BaseException("message too big: %s" % length)

        data = self.s.read(length)
        self.req.ParseFromString(data)
        head.id = self.req.id
        head.service = self.req.service
        head.method = self.req.method
        if self.req.labels:
            opts = Options()
            for v in self.req.labels:
                opts.append(Option(name=v.name, value=v.value))
            head.labels = opts
        if head.id != None and head.id > 0:
            print("%s, %s.%s(%s), labels(%s)" % (head.id, head.service, head.method, "", head.labels))

    def decode_args(self, args: List[object]):
        if self.req.args != None:
            for i, v in enumerate(self.req.args):
                args.insert(i, pickle.loads(v))

    def discard_args(self):
        return None


class Builder(CodecBuilder):

    name="proto"

    def new_client_codec(self, s: Stream, opts: Map) -> ClientCodec:
        max_msg_size = self.max_msg_size(opts)
        return ClientCodec(s=s, req=Request(), resp=Response(), max_msg_size=max_msg_size)

    def new_server_codec(self, s: Stream, opts: Map) -> ServerCodec:
        max_msg_size = self.max_msg_size(opts)
        return ServerCodec(s=s, req=Request(), resp=Response(), max_msg_size=max_msg_size)

    def max_msg_size(self, opts: Map):
        size = None
        if opts != None:
            if opts.get("max_msg_size") != None:
                size = int(opts.get("max_msg_size"))

        if size == None or size == 0:
            size = const.default_max_message_size

        return size


def init():
    register_codec("proto", Builder())
