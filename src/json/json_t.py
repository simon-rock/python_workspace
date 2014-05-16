#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
## http://www.cnblogs.com/coser/archive/2011/12/14/2287739.html
import json
def json_test1():
    #encode data
    obj = [[1,2,3],123,123.123,'abc',{'key1':(1,2,3),'key2':(4,5,6)}]
    encodedjson = json.dumps(obj)
    print type(obj), "==",repr(obj)
    print type(encodedjson), "--", encodedjson
    #decode
    decodejson = json.loads(encodedjson)
    print type(decodejson)
    print decodejson[4]['key1']
    print decodejson

def json_dump():
    data1 = {'b':789,'c':456,'a':123}
    data2 = {'a':123,'b':789,'c':456}
    d1 = json.dumps(data1,sort_keys=True)
    d2 = json.dumps(data2)
    d3 = json.dumps(data2,sort_keys=True)
    print d1
    print d2
    print d3
    print d1==d2
    print d1==d3
    # using indent to formate data
    d4 = json.dumps(data1,sort_keys=True,indent=4)
    print d4
    # separators to compression data
    print 'DATA:', repr(data1)
    print 'repr(data)             :', len(repr(data1))
    print 'dumps(data)            :', len(json.dumps(data1))
    print 'dumps(data, indent=2)  :', len(json.dumps(data1, indent=4))
    print 'dumps(data, separators):', len(json.dumps(data1, separators=(',',':')))
    # skipkeys to skip error when parse data
    data = {'b':789,'c':456,(1,2):123}
    print json.dumps(data,skipkeys=True)

class Preson(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def __repr__(self):
        return 'Preson Object name: %s, age: %d' % (self.name, self.age)

def test_preson():
    p = Preson("Peter", 22)
    print p

def object2dict(obj):
    #convert object to a dict
    d = {}
    d['__class__'] = obj.__class__.__name__
    d['__module__'] = obj.__module__
    d.update(obj.__dict__)
    #print d
    return d

def dict2object(d):
    #convert  dict to object
    if '__class__' in d:                  # you can define convert fun by self or use dict by default
        class_name = d.pop('__class__')
        module_name = d.pop('__module__')
        module = __import__(module_name)
        class_ = getattr(module, class_name)
        args = dict((key.encode('ascii'), value) for key, value in d.items()) # get args
        inst = class_(**args) #create new instance
    else:
        inst = d                          # will using dict by default
    return inst

def test_convert():
    p = Preson('Peter', 22)
    d = object2dict(p)
    print type(d),d
    o = dict2object(d)
    print type(o), o
    dump = json.dumps(p, default = object2dict)
    print type(dump), dump
    load = json.loads(dump, object_hook = dict2object)
    print load

from ordereddict import OrderedDict
def test_jsonfile():
    f = open("world.json", "r+")
    con = f.read()
    print type(con), con
#    load = json.loads(con, object_hook = dict2object)
#    load = json.loads(con, object_hook = OrderedDict)      # for python 2.6
    load = json.loads(con, object_pairs_hook = OrderedDict) # for python 2.7

    print type(load), load
if __name__ == "__main__":
    #json_test1()
    #json_dump()
    #test_preson()
    #test_convert()
    test_jsonfile()
