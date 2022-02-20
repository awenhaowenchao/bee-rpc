from enum import Enum

from bee_util.errors.error import CodedError

from bee_util.data.guid import Guid
from bee_util.data.map import Map
from bee_rpc.channel import Channel
from bee_rpc.codec import CodecBuilder, RequestHead, Request, ResponseHead, Result

from gsocketpool import Pool
from gsocketpool import TcpConnection

import gevent

"""default max connectinos"""
default_max_connections = 100
"""default max error count"""
default_max_error_count = 10

class NodeState(Enum):
    """
    fail mode
    """
    """Idle indicates the Node is idle"""
    Idle = 0
    """Ready indicates the Node is ready for work"""
    Ready = 1
    """Shutdown indicates the Node has started shutting down"""
    Shutdown = 2


class Node():

    def __init__(self, id: str, address: str, status: NodeState = NodeState.Ready, cb: CodecBuilder = None,
                 connect_timeout=5):
        self.id = id
        self.address = address
        self.status = status
        self._cb = cb
        pair = address.split(":")
        options = dict(host=pair[0], port=int(pair[1]), timeout=connect_timeout)
        self.pool: Pool = Pool(TcpConnection, options,
                               # initial_connections=1,
                               max_connections=default_max_connections,
                               reap_expired_connections=False)
        self.error_count = 0

        self.count = 1

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.connect((pair[0], int(pair[1])))

    def __str__(self):
        return "Node(id={}, address={}, status={}(value={}))".format(self.id, self.address, self.status,
                                                                     self.status.value)
    def call(self, service: str, method: str, args=[]) -> Result:

        """
        class remote method
        :param service:
        :param method:
        :param args:
        :return:
        """
        print("Node.call(service={}, method={}, args={})".format(service, method, str(args)))
        try:
            with self.pool.connection() as client:
                if not client.is_connected():
                    client.open()
                sock = client.socket
                rh = RequestHead()
                rh.id = self.count
                self.count += 1
                rh.service = service
                rh.method = method
                rh.labels = []
                r = Request(head=rh, args=args)
                cc = self._cb.new_client_codec(s=Channel(id=Guid().string(), sock=sock), opts=Map())
                cc.encode(req=r)
                rh = ResponseHead()
                cc.decode_head(rh)
                rt = Result()
                cc.decode_result(rt)
                return rt

        except Exception as e:
            self.error_count +=1
            if (self.error_count >= default_max_error_count):
                self.report_error()
            raise CodedError(code=-1, message=e.__str__(), detail=e.__str__())

    def report_error(self):
        self.status = NodeState.Shutdown
        gevent.spawn(self.hearbeat())


    def hearbeat(self):
        #TODO; heartbeat retry
        pass