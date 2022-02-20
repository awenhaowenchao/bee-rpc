import json
import time

import gevent
import grpc._cython.cygrpc
grpc._cython.cygrpc.init_grpc_gevent()
import etcd3
from etcd3 import Etcd3Client
from pipenv.vendor import semver

from bee_rpc.registry.registry import Registry, Server, RegistryError


class Etcd3Registry(Registry):

    def __init__(self, server: Server):
        self.server = server
        self._etcd = self.registry_factory()

    def registry_factory(self) -> Etcd3Client:
        if self.server == None:
            raise RegistryError("load etcd server error")
        address = self.server.address
        if address:
            return etcd3.client(host=address.split(",")[0].split(":")[0], port=int(address.split(",")[0].split(":")[1]))
        else:
            raise RegistryError("load etcd server error")

    def _svc_key(self, service):
        return '/bee/rpc/{}'.format(service)

    def _node_key(self, service, nid):
        return '/bee/rpc/{}/providers/{}'.format(service, nid)

    def register(self, service: str, nid: str, address: str, version: str, ttl: int=None):
        n_key = self._node_key(service, nid)
        ttl = self.server.heartbeat_interval
        self.heartbeat(n_key, address, version, ttl)

    def deregister(self, service: str, nid: str):
        n_key = self._node_key(service, nid)
        gevent.spawn(self._etcd.delete, n_key)
    # def discovery(self, service) -> List[Node]:
    def discovery(self, service: str, v_match_regex: str) -> dict:
        s_key = self._svc_key(service)
        # print(s_key)
        res = self._etcd.get_prefix(key_prefix=s_key)
        _result = {}
        for child in res:
            json_value = json.loads(bytes(child[0]).decode())
            address = json_value["address"]
            version = json_value["version"]
            if v_match_regex != None and v_match_regex != "":
                if not semver.match(version, v_match_regex):
                    continue
            _result[bytes(child[1].key).decode().replace(s_key + "/providers/", "")] = address
        return _result

    def heartbeat(self, key, address, version, ttl):
        # print("key=%sm address=%s version=%s" % (key, address, version))
        value = json.dumps({'address': address, 'version': version})
        lease_id = int(time.time())
        lease = self._etcd.lease(ttl, lease_id)
        r = self._etcd.put(key, bytes(value, encoding="utf-8"), lease)
        # print(self._etcd.get(key))

        def heartbeat_loop():
            sleep = int(ttl / 3)
            while 1:
                gevent.sleep(sleep)
                # TODO: refresh
                print("Refreshing lease which id is %s!" % lease_id)
                # print(self._etcd.get(key))
                lease.refresh()
                print("Refreshed lease which id is %s!" % lease_id)

        self.beat_thread = gevent.spawn(heartbeat_loop)

    def watch(self, service, callback):

        def watch_loop():

            s_key = self._svc_key(service)
            events_iterator, cancel = self._etcd.watch_prefix(s_key)
            for event in events_iterator:
                if isinstance(event, etcd3.events.DeleteEvent):
                    callback({
                        "action" : "delete",
                        "key" : event.key.decode(),
                        "value": event.value
                    })
        #todo: to be continued
        self.watch_thread = gevent.spawn(watch_loop)

    def _proc_action(self, action):
        return 'delete' if action == 'expire' else action

    def close(self):
        if hasattr(self, "beat_thread"):
            self.beat_thread.kill()
        if hasattr(self, "watch_thread"):
            self.watch_thread.kill()

def str_to_host(s):
    h, p = s.split(":")
    return (str(h), int(p))