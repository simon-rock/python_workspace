#coding: utf-8
#http://www.cnblogs.com/vamei/tag/Python/
def type_test():
    #base type
    a = 10
    d = "string"
    e = True
    f = 1.3
    # contain
    g = (1,2,3)
    b = [1,2,3]
    c = {}
    c["asdf"] = 10
    print "---base---"
    print a, type(a)
    print e, type(e)
    print f, type(f)
    print "---sequence---"
    print g, type(g)
    print b, type(b)
    print c, type(c)
    print d, type(d)
#tuple元素不可变，list元素可变
#序列的引用 s[2], s[1:8:2]
#字符串是一种tuple

if __name__ == "__main__":
    type_test()
