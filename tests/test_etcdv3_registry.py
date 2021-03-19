import gevent

from etcd3.events import DeleteEvent, PutEvent

from bee_util.data.guid import Guid
# from bee.net.rpc.registry.etcdv3_registry import Etcd3Registry
# from bee.net.rpc.registry.registry import Server
from bee_rpc import Etcd3Registry
from bee_rpc import RegistryServer as Server

server = Server(protocol="etcd3", address="127.0.0.1:2379", heartbeat_interval=10)
etcd3Registry = Etcd3Registry(server)
etcd3Registry.register("hello", Guid().string(), "127.0.0.1:8080", "2.0.0", 10)

_result = etcd3Registry.discovery("hello", ">=1.0.0")
print(_result)

_result = etcd3Registry.discovery("test", "==1.0.0")
print(_result)

# etxcd3Registry._etcd.delete_prefix("/bee/rpc");

#
# client = etcd3Registry._etcd
#
# events_iterator, cancel = client.watch_prefix('/bee/rpc', **{})
#
# for event in events_iterator:
#     print(event)
#     t = type(event)
#     if t == PutEvent:
#         print("PutEvent")
#         _result = etcd3Registry.discovery("test", ">=1.0.0")
#         print("xxxx")
#         print(_result)
#         print("xxxx")