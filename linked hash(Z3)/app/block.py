import struct


class Block(object):
    def __init__(self, blocking_factor, data=None, e=-1, u_block=-1, u_syllable=-1, b=-1, n=-1):
        self.blocking_factor = blocking_factor
        self.u_block = u_block
        self.u_syllable = u_syllable
        self.b = b
        self.n = n
        self.e = e
        if data is None:
            self.data = list()
        else:
            self.data = data

    def header_to_encoded_values(self):
        values = [self.u_block, self.u_syllable,  self.b, self.n, self.e]
        return struct.pack("iiiii", *values)

    def __str__(self):
        res = ""
        res += "u block: {0}, u syllable: {1}, b: {2}, n: {3}, e: {4}\n".format(self.u_block, self.u_syllable, self.b, self.n, self.e)
        for i, data in enumerate(self.data):
            res += str(i+1) + ". " + str(data) + "\n"
        return res

