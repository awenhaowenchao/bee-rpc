from gevent import signal
from gevent.server import StreamServer
import grpc._cython.cygrpc
grpc._cython.cygrpc.init_grpc_gevent()

from datetime import datetime
from typing import List
import logging
from bee_rpc.registry.builder import Builder
from bee_rpc.registry.registry import Server as RegistryServer

from bee_rpc.channel import Channel
from bee_rpc.codec import RequestHead, IServerCodec, Response, ResponseHead, Result, \
    Stream, get_codec
from bee_rpc.registry.direct_registry import DirectRegistry
from bee_rpc.transport import Address

from bee_util.data.guid.guid import Guid
from bee_util.data.map import Map
from bee_util.errors.error import BeeError
from bee_rpc.registry.registry import Registry
from bee_util.data import const

# from bee import config
import bee_config as config
logging.basicConfig(level=logging.DEBUG)
is_debug = True


class ServerLoadError(BeeError):
    pass


class ReadPeeker(object):
    pass


class MatchInfo():
    """
    codec macher
    """

    def __init__(self, codec: str = "proto", opts: Map = None):
        self.codec = codec
        self.opts = opts

    def match(self, p: ReadPeeker) -> bool:
        """
        偷瞄两眼，看看是什么编码，吼吼吼
        :param p:
        :return:
        """
        pass


class Session():

    def id(self) -> str:
        pass

    def local_addr(self) -> str:
        pass

    def remote_addr(self) -> str:
        pass


class session(Session):

    def __init__(self, ch: Stream, sc: IServerCodec, heartbeat: datetime = datetime.now()):
        self.channel = ch
        self.sc = sc
        self.heartbeat = heartbeat

    def id(self) -> str:
        return self.channel.id()


def new_session(ch: Stream, sc: IServerCodec) -> session:
    return session(ch=ch, sc=sc, heartbeat=datetime.now())


class SessionMap():

    def __init__(self):
        self.channels = Map()

    def add(self, s: session):
        self.channels.set(s.id(), s)

    def get(self, id: str):
        self.channels.get(id)

    def remove(self, id: str):
        self.channels.remove(id)

    def count(self):
        return len(self.channels)


class ServerOptions(Map):

    def __init__(self, name: str = None, desc: str = None, version: str = "1.0.0", macher: str = "proto",
                 address: Address = None
                 , max_conn_size: int = 1024, max_pool_size: int = 1024, backlog: int = 1000
                 , read_timeout: int = 10, write_timeout: int = 10):
        self.id = Guid().string()
        self.name = name
        self.desc = desc
        self.version = version
        self.macher = macher
        self.address = address
        self.max_conn_size = max_conn_size
        self.max_pool_size = max_pool_size
        self.backlog = backlog
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout


class Server():

    def __init__(self, opts: ServerOptions, registry: Registry = None):
        self.opts = opts

        if registry == None:
            self.registry = DirectRegistry(url=opts.address.url)
        else:
            self.registry = registry

        # 初始化service管理容器
        self.services = Map()

        # 初始化session管理容器
        self.sessions = SessionMap()

        # 初始化编解码器
        self.init_codec_builder()


    @staticmethod
    def new_server(name: str = None, macher: str = "proto", address: Address = Address(url="127.0.0.1:9000"),
                   registry: Registry = None) -> "Server":
        opts = ServerOptions(name=name, macher=macher, address=address, version="1.0.0")
        if is_debug:
            logging.debug("bee.rpc > init server's options")
        s = Server(opts=opts, registry=registry)
        if is_debug:
            logging.debug("bee.rpc > new server...")
        return s

    def register_service(self, ins):
        """register rpc service"""
        if not ins:
            return
        name = ins.__class__.__name__
        self.services.set(name, ins)

    def handle(self, sock, address):
        print("address= " + str(address))
        while True:
            if sock.closed == True:
                print("closed...")
                break
            self.handle_request(sock, address)
        sock.close()

    def init_codec_builder(self):
        if self.opts.macher == "http":
            pass
        elif self.opts.macher == "json":
            b = get_codec("json")
            if not b:
                import bee_rpc.codecs.json.json as json
                json.init()
        else:  # proto
            b = get_codec("proto")
            if not b:
                import bee_rpc.codecs.proto.proto as proto
                proto.init()

    def new_server_codec(self, sock) -> IServerCodec:
        m = self.opts.macher
        if m == None:
            raise ServerLoadError("no macher!")
        else:
            b = get_codec(m)
            if not b:
                raise ServerLoadError("init codec builder error!")
            return b.new_server_codec(s=Channel(id=Guid().string(), sock=sock), opts=Map())

    def add_session(self, sc) -> session:
        s = new_session(sc.stream(), sc)
        self.sessions.add(s)
        return s

    def remove_session(self, sc) -> session:
        self.sessions.remove(sc.stream().id())

    def handle_request(self, sock, address):
        rh = RequestHead()
        args = []
        sc = self.new_server_codec(sock)
        sc.decode_head(rh)
        if rh.id == None or rh.id == 0:
            sock.close()
        else:
            # print("rh.id=" + str(rh.id))
            sc.decode_args(args)
            self.add_session(sc)
            self.invoke_service(sc, rh=rh, args=args)
            self.remove_session(sc)

    def invoke_service(self, sc, rh: RequestHead, args: List):
        id = rh.id
        sname = rh.service
        s = self.services.get(sname)
        mname = rh.method
        if s != None:
            ret = getattr(s, mname)(*(args))
            head = ResponseHead(id=id, assets=None)
            result = Result(value=ret, error=None)
            resp = Response(head=head, result=result)
            sc.encode(resp)
        else:
            print("do nothing")

    def find_codec_builder(self, macher: str) -> IServerCodec:
        cb = const.codecs.get(macher)
        return cb

    def register(self):
        self.nid = Guid().string()
        self.registry.register(self.opts.name, self.nid, self.opts.address.url, self.opts.version)

    def handle_signal(self):
        """register signal"""
        def handler(signum, frame):
            logging.info("bee.rpc > kill service={}, nid={}".format(self.opts.name, self.nid))
            self.registry.deregister(self.opts.name, self.nid)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def startup(self):
        """
        start the rpc server
        """
        # if not self.handler:
        #     raise ServerLoadError('Methods not exits.')

        self.handle_signal()

        pair = self.opts.address.url.split(":")
        server = StreamServer(
            (pair[0], int(pair[1])),
            self.handle,
            backlog=self.opts.backlog,
            spawn=self.opts.max_conn_size)

        self.register()
        self.srv = server
        print("Start success!")
        server.serve_forever()

    def shutdown(self):
        """
        shutdown the rpc server
        """
        if self.registry != None:
            self.registry.close()

        if self.srv != None:
            self.srv.close()

    def __call__(environ, start_response):
        # for gunicorn wsgi app
        pass

def auto_server():

    if config.exist("debug"):
        is_debug = config.get("debug")
    bee_rpc_registry_conf = config.get("bee.rpc.registry")
    registry_server = RegistryServer()
    registry_server.__dict__ = bee_rpc_registry_conf
    registry = Builder.build(registry_server)

    bee_rpc_server_conf = config.get("bee.rpc.server")
    if bee_rpc_server_conf != None:
        for k, v in dict(bee_rpc_server_conf).items():
            opts = ServerOptions()
            opts.name = k
            opts.cover(Map.from_dict(v))
            srv = Server(opts=opts, registry=registry)
            srv.startup()

            logging.info("bee.rpc > server start success")

