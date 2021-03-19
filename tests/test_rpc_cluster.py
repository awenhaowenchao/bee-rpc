
from gevent import monkey
monkey.patch_socket()

from bee_rpc.client import Cluster
if __name__ == '__main__':
    cluster = Cluster()
    client = cluster.get_client("test")
    result = client.call(service="Test", method="hello", args=["awen"])
    print("result=" + str(result.value))
    result = client.call(service="Test", method="hello", args=["zhangsan"])
    print("result=" + str(result.value))
    result = client.call(service="Test", method="hello", args=["lizi"])
    print("result=" + str(result.value))
    result = client.call(service="Test", method="hello", args=["wangwu"])
    print("result=" + str(result.value))
    result = client.call(service="Test", method="hello", args=["liusi"])
    print("result=" + str(result.value))
    result = client.call(service="Test", method="test", args=[])
    print("result=" + str(result.value))

    # result = client.call(service="Test", method="test", args=[])
    # print("result=" + str(result.value))

