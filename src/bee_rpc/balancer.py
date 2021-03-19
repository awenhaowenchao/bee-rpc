import random
from typing import List

from bee_rpc.node import Node, NodeState

MaxSelectArraySize = 3
defaultWeight = 1


class RandomBalancer(object):

    def __init__(self, nodes: List[Node] = [], weight=None):
        self.nodes = nodes

    def select(self) -> Node:
        _, ep = select_one_random(self.nodes)
        return ep

    def select_list(self) -> List[Node]:
        index, ep = select_one_random(self.nodes)
        if not ep:
            return ep
        return select_list_from_index(self.nodes, index)


class RoundrobinBalancer(object):

    def __init__(self, nodes: list = [], weight=None):
        self.nodes = nodes
        self.index = 0

    def select(self) -> Node:
        _, ep = self.roundrobin_select()
        return ep

    def select_list(self) -> List[Node]:
        index, ep = self.roundrobin_select()
        if not ep:
            return ep
        return select_list_from_index(self.nodes, index)

    def roundrobin_select(self):
        nodes = self.nodes
        if not nodes:
            return -1, None

        idx = self.index % len(nodes)
        self.index += 1
        if nodes[idx].status == NodeState.Ready:
            return idx, nodes[idx]

        return select_one_random(self.nodes)


def select_one_random(nodes):
    nodes_len = len(nodes)
    if nodes_len == 0:
        return -1, None

    index = random.randint(0, nodes_len - 1)
    if nodes[index].status == NodeState.Ready:
        return index, nodes[index]

    rd = random.randint(0, nodes_len - 1)
    for i in range(nodes_len):
        rdi = (rd + i) % nodes_len
        if nodes[rdi].status == NodeState.Ready:
            return rdi, nodes[rdi]

    return -1, None


def select_list_from_index(nodes, index):
    if not nodes or index < 0:
        return []

    nodes_len = len(nodes)
    ep_list = []
    for i in range(nodes_len):
        idx = (index + i) % nodes_len
        if nodes[idx].status == NodeState.Ready:
            ep_list.append(nodes[idx])
        if len(ep_list) == MaxSelectArraySize:
            break
    return ep_list
