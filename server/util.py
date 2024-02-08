import json
import struct
import socket
from typing import Any

def send_json(s: socket.socket, data: Any):
    """
    Serializes a data as json and sends it into socket
    """
    serialized_data = json.dumps(data).encode()
    msg = struct.pack('>I', len(serialized_data)) + serialized_data
    s.sendall(msg)

def get_json(s: socket.socket) -> Any:
    """
    Gets the serialized data sent with send_json
    """
    raw_msglen = recvall(s, 4)
    if not raw_msglen:
        raise IOError("socket closed")
    msglen = struct.unpack('>I', raw_msglen)[0]
    serialized_data = recvall(s, msglen)
    return json.loads(serialized_data)

def recvall(s: socket.socket, n: int) -> bytearray:
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = s.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data