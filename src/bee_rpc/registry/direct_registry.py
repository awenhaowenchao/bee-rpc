from bee_util.data.guid import Guid
from bee_rpc.registry.registry import Registry


class DirectRegistry(Registry):
    """Fake Registry"""

    def __init__(self, url: str):
        self.url = url

    def register(self, service: str, nid: str, address: str, version: str=None, ttl: int=None):
        pass

    def deregister(self, service: str, nid: str):
        pass

    def discovery(self, service: str, v_match_regex: str):
        url = self.url
        if url:
            node = {Guid().string() : url}
            return node
        return {}
    def watch(self, service, callback):
        pass

    def close(self):
        pass