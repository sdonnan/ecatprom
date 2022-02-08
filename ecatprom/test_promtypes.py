from io import BytesIO
from promtypes import *

def test_write_read():
    buffer = BytesIO()
    r = Reader(buffer)
    w = Writer(buffer)
    a = Int(4)
    a.value = 0xA
    b = Int(16)
    b.value = 0xBEEF
    c = Int(1)
    c.value = 0
    d = Int(3)
    d.value = 6
    e = Int(16)
    e.value = 0xDEAD

    a.put(w)
    b.put(w)
    c.put(w)
    d.put(w)
    e.put(w)

    assert bytes(buffer.getbuffer()) == b'\xFA\xEE\xCB\xAD\xDE'
    buffer.seek(0)

    a.value = 0
    b.value = 0
    c.value = 0
    d.value = 0
    e.value = 0

    a.take(r)
    b.take(r)
    c.take(r)
    d.take(r)
    e.take(r)

    assert a.value == 0xA
    assert b.value == 0xBEEF
    assert c.value == 0x0
    assert d.value == 0x6
    assert e.value == 0xDEAD

    assert buffer.read() == b''

def test_int():
    buffer = BytesIO(b'\x42\xa5\xb6')
    r = Reader(buffer)
    uut = Int(2)
    uut.take(r)
    assert uut.value == 2 
    uut = NullBits(6)
    uut.take(r)
    uut = Int(16)
    uut.take(r)
    assert uut.value == 0xb6a5
    assert str(uut) == '46757(0xB6A5)'

def test_struct():
    buffer = BytesIO(b'\x42\xa5\xb6')
    r = Reader(buffer)
    uut = Struct(
        a=Int(2),
        b=Int(6),
        c=Int(16),
    )
    uut.take(r)
    assert uut.a.value == 2 
    assert uut.b.value == 4 << 2
    assert uut.c.value == 0xb6a5
    
def test_enum():
    buffer = BytesIO(b'\x01\x02\x03')
    uut = Enum(8, {1: 'A', 2: 'B'})
    r = Reader(buffer)
    uut.take(r)
    assert uut.value == 'A'
    uut.take(r)
    assert uut.value == 'B'
    uut.take(r)
    assert uut.value == None
    assert str(uut) == '???(0x3)'

def test_string():
    buffer = BytesIO(b'\x0Chello world!XXX')
    uut = String()
    r = Reader(buffer)
    uut.take(r)
    assert uut.value == b'hello world!'
