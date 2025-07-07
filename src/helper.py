import struct
import socket
import json

def encode_peers(tuples_list: list[tuple]) -> bytes:
    encoded = bytearray()
    for ip_str, port, sc_char in tuples_list:
        ip_bytes: bytes = socket.inet_aton(ip_str)

        port_bytes: bytes = struct.pack('!H', port)

        sc_byte = sc_char.encode('ascii')

        encoded.extend(ip_bytes)
        encoded.extend(port_bytes)
        encoded.extend(sc_byte)

    return bytes(encoded)

def decode_peers(encoded_bytes: bytes) -> list[tuple]:
    tuples_list: list[tuple] = []
    tuple_size: int = 7

    if len(encoded_bytes) % tuple_size != 0:
        raise ValueError("Invalid encoded peers length")

    for i in range(0, len(encoded_bytes), tuple_size):
        chunk: bytes = encoded_bytes[i:i+tuple_size]

        ip_bytes: bytes = chunk[:4]
        ip_str: str = socket.inet_ntoa(ip_bytes)

        port_bytes: bytes = chunk[4:6]
        (port,) = struct.unpack('!H', port_bytes)

        sc_char: str = chunk[6:7].decode('ascii')

        tuples_list.append((ip_str, port, sc_char))

    return tuples_list

def encode_dict(d: dict) -> bytes:
    return json.dumps(d).encode('utf-8')

def decode_dict(b: bytes) -> dict:
    return json.loads(b.decode('utf-8'))
