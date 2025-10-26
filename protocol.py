import struct
import zlib

BUFFER_SIZE = 1024
HEADER_SIZE = 12
PAYLOAD_SIZE = BUFFER_SIZE - HEADER_SIZE

MSG_TYPE_REQUEST = 1
MSG_TYPE_DATA = 2
MSG_TYPE_ACK = 3
MSG_TYPE_NAK = 4
MSG_TYPE_ERROR = 5
MSG_TYPE_FINISH = 6

def create_header(msg_type, sequence_number, checksum=0):
    return struct.pack('!I I I', msg_type, sequence_number, checksum)

def parse_header(header_bytes):
    return struct.unpack('!I I I', header_bytes)

def calculate_checksum(data):
    return zlib.crc32(data)

def create_ack_packet(sequence_number):
    header = create_header(MSG_TYPE_ACK, sequence_number)
    return header

def create_nak_packet(missing_sequence_numbers):
    nak_header = create_header(MSG_TYPE_NAK, 0)
    payload = struct.pack(f'!{len(missing_sequence_numbers)}I', *missing_sequence_numbers)
    return nak_header + payload

def parse_nak_packet(payload_bytes):
    num_integers = len(payload_bytes) // 4
    return struct.unpack(f'!{num_integers}I', payload_bytes)