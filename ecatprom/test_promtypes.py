from io import BytesIO
from promtypes import *

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
    buffer = BytesIO(b'\x0Chello world!')
    uut = String()
    r = Reader(buffer)
    uut.take(r)
    assert uut.value == 'hello world!'
