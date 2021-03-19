import pickle

import six

from  bee_rpc.codecs.proto.msg_pb2 import *

request = Request()
request.id = 1000
request.service = "test"
request.method = "test"
request.labels.append(Label(name="label", value="label"))
request.labels.append(Label(name="label1", value="label1"))
request.args.append(b"hello")
request.args.append(b" world")
request.args.append(b"!")
# request.args.append(six.int2byte(1))
request.args.append(pickle.dumps(1))

print(request.SerializeToString())
print(int(2 << 20).bit_length())
print("------------")
# print(bytes("4".encode("utf-8")).decode())
# print(bytearray(4))
# print(six.int2byte(56))
print(bytearray(int(6666).to_bytes(4, byteorder='little')))
print(int.from_bytes(b'\n\x1a\x00\x00', byteorder='little'))
print("------------")
print(hex(1000))


request1 = Request()
request1.ParseFromString(b'\x08\xe8\x07\x12\x04test\x1a\x04test"\x0e\n\x05label\x12\x05label"\x10\n\x06label1\x12\x06label1*\x05hello*\x06 world*\x01!*\x01\x01')
print(request1)

for i in [3,2,5]:
    print(i)

print(bytes("hello world", encoding="utf-8"))

request.ParseFromString(b'\x08\xe8\x07\x12\x04test\x1a\x04test"\x0e\n\x05label\x12\x05label"\x10\n\x06label1\x12\x06label1*\x05hello*\x06 world*\x01!*\x01\x01')
print(request)