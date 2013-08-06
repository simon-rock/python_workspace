import re
import string
strr = "translate(57.077812,12.405725) scale(1.530265,1.530265)"
prog = re.compile("(\S+)\((\S+),(\S+)\)\s+(\S+)\((\S+),(\S+)\)")
prog_s = re.compile("translate\((\S+),(\S+)\)")
res = re.match(prog, strr)
print res
tu = res.groups()
for item in range(len(tu)):  
    print tu[item] 

#test
print "------", strr
res = re.search(prog_s, strr)
if len(res.groups()) == 2:
    #x = string.atof(res.group(1))
    #x = float(res.groups()[0])
    #y = string.atof(res.groups()[1])
    x = float(res.group(1)) * 2
    y = float(res.group(2)) * 2
    print "new value", x, y
    xstr = "translate(%f,%f)" % (x, y)
    xtu = (xstr, xstr)
    print re.search(prog_s, strr).groups()
    newstr = re.sub(prog_s, xtu, strr)
    print newstr

#use
prog_scale = re.compile("scale\((\S+),(\S+)\)")
res = re.search(prog_scale, strr)
if len(res.groups()) == 2:
    x = float(res.group(1)) * 2
    y = float(res.group(2)) * 2
    scale = "scale(%f,%f)" % (x, y)
    new = re.sub(prog_scale, scale, strr)
    print new

#http://bbs.csdn.net/topics/330087864
