from bee_rpc import ConsulRegistry
from bee_rpc import Etcd3Registry
from bee_rpc import RegistryServer as RServer
from bee_rpc.server import Server
from bee_rpc.transport import Address

etcd = Etcd3Registry(RServer(protocol="etcd3", address="127.0.0.1:2379", heartbeat_interval=30))
srv = Server.new_server(name="test", macher="proto", address=Address(url="127.0.0.1:9000"), registry=etcd)
# server = RServer(protocol="consul", address="127.0.0.1:8500", heartbeat_interval=30)
# cr = ConsulRegistry(server)
# srv = Server.new_server(name="test", macher="proto", address=Address(url="127.0.0.1:9000"), registry=cr)

class Test():
    def hello(self, name):
        return "hello " + name

    #classmethod & staticmethod不支持
    @classmethod
    def hello1(cls):
        print( "hello")

    @staticmethod
    def hello2(arg1, arg2):
        print("hello")

    def test(self):
    #    return "test"
        pass


srv.register_service(Test())
srv.startup()