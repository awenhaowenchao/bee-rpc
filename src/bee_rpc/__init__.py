#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'wenchao.hao'

"""
net.rpc package. include json、protobuff、http(to be continued) codec

"""


from .registry.registry import Server as RegistryServer
from .registry.consul_registry import ConsulRegistry
from .registry.etcdv3_registry import Etcd3Registry