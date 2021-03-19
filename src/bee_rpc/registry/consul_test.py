from bee_util.data.guid import Guid
from bee_rpc.registry.consul_registry import ConsulRegistry
from bee_rpc.registry.registry import Server

server = Server(protocol="consul", address="127.0.0.1:8500", heartbeat_interval=30)
cr = ConsulRegistry(server)

cr.register(service="test", nid=Guid().string(), address="127.0.01:9999", ttl=server.heartbeat_interval)

services = cr.discovery(service="test")
print(services)

cr.deregister('test', 'bmv9kqb24te0m4j24srg')
