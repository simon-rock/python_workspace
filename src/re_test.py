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

res = re.search(prog_s, strr)

print "-----"
if len(res.groups()) == 2:
    #x = string.atof(res.group(1))
    #x = float(res.groups()[0])
    #y = string.atof(res.groups()[1])
    x = float(res.group(1))
    y = float(res.group(2))
    print "sf"
    

print x , y


#http://bbs.csdn.net/topics/330087864
