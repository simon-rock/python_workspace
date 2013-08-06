#coding: utf8
import re
import string
strr = "translate(57.077812,12.405725) scale(1.530265,1.530265)"
prog = re.compile("(\S+)\((\S+),(\S+)\)\s+(\S+)\((\S+),(\S+)\)")
prog_s = re.compile("translate\((\S+),(\S+)\)")
#prog_s = re.compile("\S+\((\S+),(\S+)\)")

#match
res = re.match(prog, strr)
print res.group(0)
tu = res.groups()
print tu
for item in range(len(tu)):  
    print tu[item] 

#search and sub
print "------", strr
res = re.search(prog_s, strr)
print res.group(0)
if len(res.groups()) == 2:
    #x = string.atof(res.group(1))
    #x = float(res.groups()[0])
    #y = string.atof(res.groups()[1])
    x = float(res.group(1)) * 2
    y = float(res.group(2)) * 2
    print "new value:", res.group(0),x, y
    xstr = "translate(%f,%f)" % (x, y)
    xtu = (xstr, xstr)
    newstr = re.sub(prog_s, xtu, strr)
    print newstr
    newstr = re.sub(prog_s, xstr, strr)
    print newstr

#use
prog_scale = re.compile("scale\((\S+),(\S+)\)")
res = re.search(prog_scale, strr)
if res and len(res.groups()) == 2:
    x = float(res.group(1)) * 2
    y = float(res.group(2)) * 2
    scale = "scale(%f,%f)" % (x, y)
    new = re.sub(prog_scale, scale, strr)
    print new

def displaymatch(match):
    if match is None:
        return None
    return '<Match: %r, groups=%r>' % (match.group(), match.groups())

print "-----test-----"
text = "JGood is a handsome boy, he is cool, clever, and so on..."
#对于python的正则，特别之处在于正册匹配时可以用括号表示分组从group（）获得其值
#match search 都为贪婪匹配 找到一个返回
print displaymatch(re.match(r"(\w+)\s", text))
print displaymatch(re.match(r"\w+\s", text))
print displaymatch(re.search(r'\shan(ds)ome\s', text))
print re.sub(r'\s+', '-', text)
print re.sub(r'\s', lambda m: '[' + m.group(0) + ']', text, 0)
print re.split(r'\s+', text)
print re.findall(r'\w*oo\w*', text)

#diff match search
s1="helloworld, i am 30 !"
w1 = "world"
print displaymatch(re.match(w1, s1))
print displaymatch(re.search(w1, s1))


#split findall finditer sub  
s1 = "i am working in microsoft !"
l = re.split('\s+', s1) # l is list type
print( l)
  
s2 = "aa 12 bb 3 cc 45 dd 88 gg 89"
l2 = re.findall('\d+', s2)
print(l2)
  
it = re.finditer('\d+', s2) # it is one iterator type
for i in it: # i is matchobject type
    print (i.group())
    
s3 = re.sub('\d+', '200', s2)
print(s3)
#http://bbs.csdn.net/topics/330087864
