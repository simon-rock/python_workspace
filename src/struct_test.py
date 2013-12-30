#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
#http://www.cnblogs.com/coser/archive/2011/12/17/2291160.html
import struct
import binascii
import ctypes
def pack_unpack():
    values = (1, 'abc', 2.7)
    s = struct.Struct('I3sf')
    #s = struct.Struct(‘<I3sf’) #小端存储 
    packed_data = s.pack(*values)
    unpacked_data = s.unpack(packed_data)
    print 'Original values:', values
    print 'Format string :', s.format
    print 'Uses :', s.size, 'bytes'
    print 'Packed Value :', binascii.hexlify(packed_data)
    print 'Unpacked Type :', type(unpacked_data), ' Value:', unpacked_data
    #*********************
    #Code Meaning
    #@    Native order
    #=    Native standard
    #<    Little-endian
    #>    Big-endian
    #！   Network order
    #*********************
    
def packwithbuffer():
    values = (1, 'abc', 2.7)
    s = struct.Struct('I3sf')
    prebuffer = ctypes.create_string_buffer(s.size)
    print 'Before :',binascii.hexlify(prebuffer)
    s.pack_into(prebuffer,0,*values)
    print 'After pack:',binascii.hexlify(prebuffer)
    unpacked = s.unpack_from(prebuffer,0)
    print 'After unpack:',unpacked

def packwithoffset():
    values1 = (1, 'abc', 2.7)
    values2 = ('defg',101)
    s1 = struct.Struct('I3sf')
    s2 = struct.Struct('4sI')
    prebuffer = ctypes.create_string_buffer(s1.size+s2.size)
    print 'Before :',binascii.hexlify(prebuffer)
    s1.pack_into(prebuffer,0,*values1)
    s2.pack_into(prebuffer,s1.size,*values2)
    print 'After pack:',binascii.hexlify(prebuffer)
    print s1.unpack_from(prebuffer,0)
    print s2.unpack_from(prebuffer,s1.size)
    
if __name__ == "__main__":
    print "--pack_unpack--"
    pack_unpack()
    print "--packwithbuffer--"
    packwithbuffer()
    print "--packwothoffset--"
    packwithoffset()
    
