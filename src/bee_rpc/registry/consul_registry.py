import gevent
from pipenv.vendor import semver

from consul import Consul
from bee_util.gevent import patch_greenlet
from bee_rpc.registry.registry import Registry, Server, RegistryError


class ConsulRegistry(Registry):


    def __init__(self, server: Server):
        self.server = server
        self.client = self.registry_factory()

    def registry_factory(self) -> Consul:
        if self.server == None:
            raise RegistryError("load etcd server error")
        address = self.server.address
        if address:
            return Consul(host=address.split(",")[0].split(":")[0], port=int(address.split(",")[0].split(":")[1]))
        else:
            raise RegistryError("load etcd server error")

    def _svc_key(self, service):
        return '/bee/rpc/{}'.format(service)

    def _node_key(self, service, nid):
        return '/bee/rpc/{}/providers/{}'.format(service, nid)

    def register(self, service: str, nid: str, address: str, version: str, ttl: int=None):
        self.client.agent.service.register(name=service, service_id=nid
                                           , address=address.split(",")[0].split(":")[0]
                                           , port=int(address.split(",")[0].split(":")[1])
                                           , tags=[version]
                                           , enable_tag_override=True
                                           )

    @patch_greenlet
    def deregister(self, service: str, nid: str):
        self.client.agent.service.deregister(nid)

    # def discovery(self, service) -> List[Node]:
    def discovery(self, service: str, v_match_regex: str) -> dict:

        # dns mode
        # from dns import resolver
        # from dns.exception import DNSException
        # consul_resolver = resolver.Resolver()
        # consul_resolver.port = 8600
        # consul_resolver.nameservers = ["127.0.0.1"]
        # dnsanswer_srv = consul_resolver.Query(f"{service}.service.consul", "SRV")
        # print(dnsanswer_srv.response)

        # http mode
        # requests.get(f"http://localhost:8500/v1/catalog/service/{service}")
        res = self.client.catalog.service(service=service)
        services = res[1]
        _result = {}
        for child in services:
            if v_match_regex != None and v_match_regex != "":
                if not semver.match(str(child["ServiceTags"][0]), v_match_regex):
                    continue
            _result[child["ServiceID"]] = child["ServiceAddress"] + ":" + str(child["ServicePort"])
        return _result

        # return {child["ServiceID"] : child["ServiceAddress"] + ":" + str(child["ServicePort"]) for child in services}

    def heartbeat(self, key, value, ttl):
        #todo: to be continued
        pass

    def watch(self, service, callback):
        def watch_loop():
            #todo: to be continued
            # print(self.client.health.service(service))
            pass
        self.watch_thread = gevent.spawn(watch_loop)

    def _proc_action(self, action):
        return 'delete' if action == 'expire' else action

    @patch_greenlet
    def close(self):
        if hasattr(self, "beat_thread"):
            self.beat_thread.kill()
        if hasattr(self, "watch_thread"):
            self.watch_thread.kill()