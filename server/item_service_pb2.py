# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: item_service.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12item_service.proto\x12\x04item\x1a\x1bgoogle/protobuf/empty.proto\"\"\n\x04Item\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t2a\n\x0bItemService\x12\"\n\x08PushItem\x12\n.item.Item\x1a\n.item.Item\x12.\n\x08PullItem\x12\x16.google.protobuf.Empty\x1a\n.item.Itemb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'item_service_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_ITEM']._serialized_start=57
  _globals['_ITEM']._serialized_end=91
  _globals['_ITEMSERVICE']._serialized_start=93
  _globals['_ITEMSERVICE']._serialized_end=190
# @@protoc_insertion_point(module_scope)
