#coding: utf8
import re
import string

#http://bbs.csdn.net/topics/330087864
    
def recalculate_scale():
    #将倍率取出，计算后再替换回去
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


def basic_test():
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
    


def displaymatch(match):
    if match is None:
        return None
    return '<Match: %r, groups=%r>' % (match.group(), match.groups())

def parse_pattern(pattern):
    '''parse pattern line'''
    '''[0:10]=0123456789 and ([12:2]=22 or [12:2])=25'''

    exp_list = []
    op_list = []
    while len(pattern):
        #print "--pattern--", pattern
        if pattern.startswith(' '):
            pattern = pattern.lstrip()

        if pattern.startswith('('):
            m = re.match('\((.*?)\)\s*(or|and)?', pattern, re.I)
            #print "-2-",displaymatch(m)
            if m:
                sub_pattern, op = m.groups()
                #print sub_pattern, op
                exp_list.append(sub_pattern)
                op_list.append(op)
                #parse_pattern1(pattern[m.endpos+1::], patlist)
                pattern = pattern[m.span()[1]+1::]
            else:
                break;

        else:
            m = re.match('(\[\d+:\d+\](<=|>=|>|<|=|!=)\S*)\s*(or|and)?', pattern, re.I)
            #print "-1-",displaymatch(m)
            if m:
                sub_pattern, key, op = m.groups()
                exp_list.append(sub_pattern)
                op_list.append(op)
                #parse_pattern1(pattern[m.endpos+1::], patlist)
                pattern = pattern[m.span()[1]+1::]
            else:
                break

        if not pattern:
            break

    return (exp_list, op_list)

def matchall(line, statement_list, op_list):
    '''match all statement'''

    bRes =False
    index = 0
    statement = statement_list[0]
    op = op_list[0]
    bRes = matchone(line, statement)

    while index < len(statement_list):
        if not op:
            break

        index = index + 1

        statement = statement_list[index]
        if not statement:
            break

        if (bRes and op == 'or') or (not bRes and op == 'and'):
            pass
        else:
            if op == 'and':
                bRes &= matchone(line, statement)

            elif op == 'or':
                bRes |= matchone(line, statement)

        op = op_list[index]
        
    return bRes


def get_exp_result(line, statment):
    '''get exp result'''
    format = '\[(\d+):(\d+)\](<=|>=|>|<|=|!=)(.*)'
    reCmd = re.compile(format, re.I)
    bRes = False
    #print (statment, op)
    m = reCmd.search(statment)
    if m:
        pos, length, key, value = m.groups()
        pos = int(pos)
        length = int(length)

        if pos:
            pos = pos - 1

        #print line[pos : pos+len], '<<>>', value
        if key == '=':
            bRes = (line[pos : pos + length] == value)

        elif key == '!=':
            bRes = (line[pos : pos + length] != value)

        elif key == '>':
            bRes = (line[pos : pos + length] > value)

        elif key == '>=':
            bRes = (line[pos : pos + length] >= value)

        elif key == '<':
            bRes = (line[pos : pos + length] < value)

        elif key == '<=':
            bRes = (line[pos : pos + length] <= value)

        else:
            print 'not support op'

    return bRes

def matchone(line, statement):
    '''pares statement'''

    statement_list = []
    op_list = []

    while len(statement):

        m = re.match('(\[\d+:\d+\](<=|>=|>|<|=|!=)\S*)\s*(or|and)?', statement, re.I)
        if m:
            #print displaymatch(m)
            #print m.span()
            sub_pattern, key, op = m.groups()
            statement_list.append(sub_pattern)
            op_list.append(op)
            statement = statement[m.span()[1]+1::]
            #print statement
        else:
            break

    bRes =False
    index = 0
    statement = statement_list[index]
    op = op_list[index]
    bRes = get_exp_result(line, statement)

    while index < len(statement_list):
        if not op:
            break

        index = index + 1

        statement = statement_list[index]
        if not statement:
            break

        if (bRes and op == 'or') or (not bRes and op == 'and'):
            pass
        else:
            if op == 'and':
                bRes &= get_exp_result(line, statement)

            elif op == 'or':
                bRes |= get_exp_result(line, statement)

        op = op_list[index]

    return bRes

def test(argv=None):

    exp_list, op_list = parse_pattern('[10000:10]=0120903514 or ([24:2]<=22 and [24:2]>=16) and [1:2]=10')
    print exp_list, op_list

    print matchall('012090351400000000000001800000050196949005019695300005561LB 0021009497002100949794597'
    '      94597      020200210094950021009495 N000000000000000000N000N', exp_list, op_list)


if __name__ == "__main__":
    test()
