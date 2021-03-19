from bee_rpc.balancer import RandomBalancer, RoundrobinBalancer
from bee_rpc.node import Node, NodeState

{'/bee/rpc/test/providers/': '127.0.0.1:8000'}

rb = RandomBalancer(nodes=[Node(id="1", address="127.0.0.1:8000", status=NodeState.Ready), Node(id="2", address="127.0.0.1:8000", status=NodeState.Ready), Node(id="3", address="127.0.0.1:8000", status=NodeState.Ready)])
print(rb.select())
print(rb.select())
print(rb.select())


rrb = RoundrobinBalancer(nodes=[Node(id="1", address="127.0.0.1:8000", status=NodeState.Ready), Node(id="2", address="127.0.0.1:8000", status=NodeState.Ready), Node(id="3", address="127.0.0.1:8000", status=NodeState.Ready)])
print(rrb.select())
print(rrb.select())
print(rrb.select())