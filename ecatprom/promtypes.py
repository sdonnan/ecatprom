import struct


class OutOfBytesError(Exception):
    pass


class Reader:

    def __init__(self, readable, bits_per_byte=8):
        self._data = readable
        self.pos_bits = 0
        self.bytes_buffer = 0
        self.bpb = bits_per_byte

    def read_bytes(self, n):
        '''Read n bytes'''
        if self.pos_bits != 0:
            raise ValueError('Cant read bytes until byte aligned')
        d = self._data.read(n)
        if len(d) != n:
            raise OutOfBytesError()
        return d

    def read_bits(self, n):
        '''Read n bits, little endian, least significant bit first each byte

        Once bits are read, bytes cannot be read until all bits from the byte are consumed
        '''
        if n > 64 or n < 1:
            raise ValueError('Cowardly refusing to read that many bits')
        pos = n-1
        val = 0
        while n > 0:
            if self.pos_bits <= 0:
                d = self._data.read(1)
                if len(d) != 1:
                    raise OutOfBytesError()
                self.bytes_buffer = struct.unpack('b', d)[0]
                self.pos_bits = self.bpb
            self.pos_bits -= 1
            val = val >> 1
            val = (val | (self.bytes_buffer & 1) << pos)
            self.bytes_buffer = (self.bytes_buffer >> 1)
            n -= 1
        return val


class Writer:

    def __init__(self, writeable, bits_per_byte=8):
        self._data = writeable
        self.pos_bits = 0
        self.bytes_buffer = 0
        self.bpb = bits_per_byte

    def flush(self):
        self.write_bytes(b'')

    def write_bytes(self, d):
        '''Write bytes'''
        if self.pos_bits == self.bpb:
            nn = self._data.write(self.bytes_buffer.to_bytes(1, 'little'))
            print('wrote', hex(self.bytes_buffer))
            if nn != 1:
                raise OutOfBytesError()
            self.pos_bits = 0
            self.bytes_buffer = 0
        elif self.pos_bits != 0:
            raise ValueError('Cant write bytes until byte aligned')
        nn = self._data.write(d)
        print('wrote', d)
        if len(d) != nn:
            raise OutOfBytesError()
        return

    def write_bits(self, val, n):
        '''Write n bits, little endian, least significant bit first each byte

        Once bits are written, bytes cannot be written until all bits for the byte are written
        '''
        if n > 64 or n < 1:
            raise ValueError(
                'Cowardly refusing to write that many bits ({})'.format(n))
        # if we can write full bytes lets just do that
        try:
            if n % self.bpb == 0:
                self.write_bytes(val.to_bytes(n//self.bpb, 'little'))
                return
        # if we are unaligned we can still write bit by bit
        except ValueError:
            pass
        # otherwise we gotta do stuff bit by bit
        while n > 0:
            if self.pos_bits == self.bpb:
                # write bytes will write and clear the state if a full byte is ready for writing
                self.write_bytes(b'')
            self.bytes_buffer |= ((val & 1) << self.pos_bits)
            self.pos_bits += 1
            val = val >> 1
            n -= 1
        return


# basically all our types can be serialized and deserialized
class Item:

    def take(self, reader):
        pass

    def put(self, writer):
        pass


class NullBytes:
    '''Throw away data'''

    def __init__(self, n, write_ones=False):
        self.n = n
        self.write_ones = write_ones

    def take(self, reader):
        reader.read_bytes(self.n)

    def put(self, writer):
        b = b'\xFF' if self.write_ones else b'\x00'
        writer.write_bytes(b*self.n)

    def __str__(self):
        return 'NullBytes({})'.format(self.n)


class NullBits(NullBytes):
    '''Throw away data'''

    def take(self, reader):
        reader.read_bits(self.n)

    def put(self, writer):
        b = 0xffffffffffffffff if self.write_ones else 0
        writer.write_bits(b, self.n)

    def __str__(self):
        return 'NullBits({})'.format(self.n)

# store numbers


class Int(Item):

    def __init__(self, bits, bounds=None):
        self.bits = bits
        self._value = 0
        self.bounds = None

    def take(self, reader):
        self._value = reader.read_bits(self.bits)

    def put(self, writer):
        writer.write_bits(self._value, self.bits)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if self.bounds:
            if v < min(self.bounds) or v > max(self.bounds):
                raise ValueError(
                    "Value {} out of bounds {}".format(v, self.bounds))
        self._value = v

    def __str__(self):
        return '{}(0x{:X})'.format(self._value, self._value)


class Enum(Int):

    def __init__(self, bits, options):
        '''
        bits - number of bits in serialized form
        options - {int: obj} dict where int is the numeric representation and object is anything
        '''
        self.bits = bits
        self._value = tuple(options.keys())[0]
        self.options = options

    @property
    def value(self):
        try:
            return self.options[self._value]
        except KeyError:
            return None

    @value.setter
    def value(self, v):
        if v not in self.options.values():
            raise ValueError("Value {} not a valid enumeration {}".format(
                v, self.options.values()))
        for k, vv in self.options.items():
            if vv == v:
                self._value = k
                return
        raise RuntimeError('This should never happen')

    def __str__(self):
        n = self.value
        if n == None:
            n = '???'
        return n + '(0x{:X})'.format(self._value)


class Struct(Item):

    def __init__(self, **kwargs):
        self._members = kwargs
        if 'put' in kwargs.keys() or 'take' in kwargs.keys():
            raise ValueError('You used a reserved member name')

    def take(self, reader):
        for v in self._members.values():
            v.take(reader)

    def put(self, writer):
        for v in self._members.values():
            v.put(writer)

    def __getattr__(self, k):
        try:
            return self._members[k]
        except KeyError:
            raise AttributeError('This struct has no member "{}"'.format(k))

    def __str__(self):
        s = []
        for k, v in self._members.items():
            lines = list(str(v).splitlines())
            if len(lines) == 1:
                s.append("{}: {}".format(k, lines[0]))
            else:
                s.append("{}:".format(k))
                for l in lines:
                    s.append('  ' + l)
        return '\n'.join(s)


class String(Item):

    def __init__(self):
        self._value = ""

    def take(self, reader):
        slen = Int(8)
        slen.take(reader)
        l = slen.value
        self._value = reader.read_bytes(l)

    def put(self, writer):
        r = self._value
        writer.write_bytes(len(r).to_bytes(1, 'little') + r)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        r = v.encode('utf8')
        if len(r) > 255:
            raise ValueError('String too long')
        self._value = r

    def __str__(self):
        return '{}'.format(self._value)


class Array(Struct):

    def __init__(self, item_type, count=None, length_prefixed=False):
        self._members = []
        self._count = count
        self._type = item_type
        self.length_prefixed = length_prefixed

    def take(self, reader):
        if self.length_prefixed:
            l = Int(8)
            l.take(reader)
            self._count = l.value
        if self._count:
            for _ in range(self._count):
                d = self._type()
                d.take(reader)
                self._members.append(d)
        else:
            while True:
                try:
                    d = self._type()
                    d.take(reader)
                    self._members.append(d)
                except OutOfBytesError:
                    break

    def put(self, writer):
        if self.length_prefixed:
            l = Int(8)
            l.value = len(self)
            l.put(writer)
        for v in self._members:
            v.put(writer)

    def __getitem__(self, k):
        return self._members[k]

    def __setitem__(self, k, v):
        self._members[k] = v

    def __len__(self):
        return len(self._members)

    def __str__(self):
        s = []
        for vi, v in enumerate(self._members):
            lines = list(str(v).splitlines())
            if len(lines) == 1:
                s.append("{}: {}".format(vi, lines[0]))
            else:
                s.append("{}:".format(vi))
                for l in lines:
                    s.append('  ' + l)
        return '\n'.join(s)
