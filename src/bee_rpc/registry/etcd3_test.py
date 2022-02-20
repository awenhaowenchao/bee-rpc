import time

import etcd3
#往etcd中存数据
from etcd3.events import DeleteEvent

client = etcd3.client(host='localhost')   #连接etcd
r  = client.put('aaa', 'qweqwe')              #往etcd中存键值
b = client.get('aaa')                        #查看etcd中的键值

print(r)
print(b)
events_iterator, cancel = client.watch('aaa')

lease_id = int(time.time())
ttl = 10
lease = client.lease(ttl, lease_id)
client.put('aaa', '111', lease)
time.sleep(8)
print(client.get("aaa"))
next(client.refresh_lease(lease_id))
time.sleep(4)

print(client.get("aaa"))




# time.sleep(1000)
# client.delete('aaa')
# for event in events_iterator:
#     print(event)
#     t = type(event)
#     if t == DeleteEvent:
#         print("删除")
#
# #监听etcd中aaa键 是否发生改变，
# for x in client.get_all(keys_only=True):
#     print(x[1].key)
#
# # res = client.delete_prefix(prefix="")
# # print(res)
#
# for y in (client.prefix(key_prefix="/bee/rpc/test/providers")):
#     print(y[1])
#
#
# m = {bytes(child[1].key).decode(): bytes(child[0]).decode() for child in client.prefix(key_prefix="/bee/rpc/test/providers")}
# # m = [bytes(child[1].key).decode() for child in client.prefix(key_prefix="/bee/rpc/test/providers")]
# print(m)
# print([x for x in {bytes(child[1].key).decode(): bytes(child[0]).decode() for child in client.prefix(key_prefix="/bee/rpc/test/providers")}.items()])

# client.delete_prefix(prefix="/bee/rpc/test/providers")