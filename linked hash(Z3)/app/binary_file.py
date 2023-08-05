#!/usr/bin/python

import struct

class BinaryFile:
    def __init__(self, filename, record, blocking_factor, block_header_size, empty_key=-1):
        self.filename = filename
        self.record = record
        self.record_size = struct.calcsize(self.record.format)
        self.blocking_factor = blocking_factor
        self.block_header_size = block_header_size
        self.block_size = self.block_header_size + self.blocking_factor * self.record_size
        self.empty_key = empty_key
