#!/bin/bash
# Generate Python protobuf code from .proto file
# Requires: pip install grpcio-tools
python -m grpc_tools.protoc -I proto --python_out=. proto/myprotocol.proto
echo "Generated myprotocol_pb2.py"
