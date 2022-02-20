from enum import Enum
from typing import List

from gevent.lock import BoundedSemaphore
import grpc._cython.cygrpc
grpc._cython.cygrpc.init_grpc_gevent()


from bee_util.data.option import Options
from bee_util.data.map import Map
from bee_util.errors.error import BeeError
from bee_rpc.balancer import RoundrobinBalancer, RandomBalancer
from bee_rpc.codec import get_codec, Result
from bee_rpc.node import Node
from bee_rpc.registry.builder import Builder
from bee_rpc.registry.direct_registry import DirectRegistry
from bee_rpc.registry.builder import Registry, Server
from bee_rpc.transport import Address

# from bee_config import config
import bee_config as config

"""default max retry times"""
default_max_retries = 3

class RemoteError(BeeError):
    pass

class FailMode(Enum):
    """
    fail mode
    """
    """FailFast returns error immediately"""
    FailFast = 0
    """FailOver selects another server automatically"""
    FailOver = 1
    """FailTry use current client again"""
    FailTry = 2



class CodecOption(Map):

    def __init__(self, name: str = None, options: Options = None):
        self.name: str = name
        self.options: Options = options


class ClientOptions(Map):

    def __init__(self, name: str = None, version: str = None, fail: str = "failover", address: Address = None
                 , codec: CodecOption = CodecOption(name="proto"), balancer: str = "random"
                 , connect_timeout: int = 5, read_timeout: int = 10, write_timeout: int = 10):
        self.name = name
        self.version = version
        self.fail = fail
        self.address = address
        self.codec = codec
        self.balancer = balancer
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout


class Client():

    def __init__(self, opts: ClientOptions, registry: Registry = None):

        # print("opts={name=%s, version=%s, fail=%s, address=%s, codec=%s, balancer=%s}" % (opts.name, opts.version, opts.fail, opts.address, opts.codec.name, opts.balancer))

        self.opts = opts

        if registry == None:
            self.registry = DirectRegistry(url=opts.address.url)
        else:
            self.registry = registry

        # init codec
        self.init_codec_builder()

        self.init_nodes()

        # init cluster's fail mode
        self.init_fail()

        # init balancer
        self.init_balancer(self.nodes)

        self.watch()

    def init_nodes(self):
        n_dict = self.registry.discovery(self.opts.name, self.opts.version)
        nodes = []
        for k, v in n_dict.items():
            node = Node(id=k, address=v, cb=get_codec(self.opts.codec.name))
            nodes.append(node)
        self.nodes = nodes


    def init_codec_builder(self):
        if self.opts.codec.name == "http":
            pass
        elif self.opts.codec.name == "json":
            b = get_codec("json")
            if not b:
                import bee_rpc.codecs.json.json as json
                json.init()
        else:  # proto
            b = get_codec("proto")
            if not b:
                import bee_rpc.codecs.proto.proto as proto
                proto.init()

    def init_fail(self):
        if self.opts.fail == "failover" :
            self.fail_mode = FailMode.FailOver
        elif self.opts.fail == "failfast" :
            self.fail_mode = FailMode.FailFast
        else:
            self.fail_mode = FailMode.FailTry

    def init_balancer(self, nodes):
        if self.opts.balancer == None or self.opts.balancer == "round-robin":
            self._lb = RoundrobinBalancer(self.nodes)
        if self.opts.balancer == "random":
            self._lb = RandomBalancer(self.nodes)

    def watch(self):
        self.registry.watch(self.opts.name, self.notify)

    def notify(self, event):
        action = event['action']
        key = str(event['key'])
        value = str(event['value'])
        if action == "delete":
            for i in self.nodes:

                if key.find(i.id) != -1:
                    self.nodes.remove(i)
                    self._lb.nodes=self.nodes
                    break
        if action == "put":
            _contains = False
            for i in self.nodes:
                if key.find(i.id) != -1:
                    _contains = True
            if not _contains:
                node = Node(id=key[key.rfind("/")+1: ], address=value, cb=get_codec(self.opts.codec.name))
                self.nodes.append(node)
                self._lb.nodes = self.nodes

    @staticmethod
    def new_client(name: str = None, address: Address = Address(url="127.0.0.1:9000"),
                   registry: Registry = None) -> "Client":
        opts = ClientOptions(name=name, address=address)
        return Client(opts=opts, registry=registry)

    def call(self, service: str, method: str, args: List[object]) -> Result:

        if self.fail_mode == FailMode.FailFast:
            return self.retry(retry=0, retried=0, change_node=False, call_param=(service, method, args))
        elif self.fail_mode == FailMode.FailOver:
            return self.retry(retry=default_max_retries, retried=0, change_node=True, call_param=(service, method, args))
        else:
            return self.retry(retry=default_max_retries, retried=0, change_node=False, call_param=(service, method, args))



    def retry(self, retry=0, retried=0, change_node=False, call_param:tuple=()):
        """

        :param retry: 重试次数
        :param retried: 已重试次数
        :param change_node: 是否切换节点
        :param call_param: 调用参数(元组) service, method, args
        :return:
        """
        node = self._lb.select()
        try:
            if not node:
                raise RemoteError("no server's ready")
            result = node.call(service=call_param[0], method=call_param[1], args=call_param[2])
            return result
        except Exception as e:
            if retry > 0 and retried < retry:
                return self.retry(retry, retried, change_node, call_param)
            raise RemoteError("no server's ready")

class Cluster(object):
    """
        client-side cluster
        manage all client
    """

    def __init__(self):
        """Cluster 抽象"""
        self.sem = BoundedSemaphore(1)
        self._clients = {}
        self.init_config()

    def get_client(self, service) -> Client:
        if not service in self._clients:
            self.sem.acquire()
            if not service in self._clients:
                self._clients[service] = Client(self.context, service)
            self.sem.release()
        return self._clients[service]

    def init_config(self):
        bee_rpc_registry_conf = config.get("bee.rpc.registry")
        if bee_rpc_registry_conf == None:
            raise BeeError("Please check app.yml exist or not?")
        server = Server()
        server.__dict__ = bee_rpc_registry_conf
        self.registry = Builder.build(server)

        bee_rpc_client_conf = config.get("bee.rpc.client")
        if bee_rpc_client_conf != None:
            for k, v in dict(bee_rpc_client_conf).items():
                opts = ClientOptions()
                opts.name = k
                opts.cover(Map.from_dict(v))
                self._clients[k] = Client(opts=opts, registry=self.registry)


