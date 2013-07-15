#-*- coding: utf-8 -*-
#!/usr/bin/env python

# ====================================================================
#
# svnchanged_export.py
#
# Export Files in a revision Range
# Usage: svnchanged_export.py -r beginRev:endRev --username user --password passwd url targetPath
# Author: Rock Sun( http://rocksun.cn )
# Site: http://rocksun.cn/svnchanged-export/
# example: svnchanged_export.py -r 1872:1873 -u gaoyu -p 111111 url targetPath
# ====================================================================

import pysvn # http://pysvn.tigris.org/
import getopt, sys, time, string
import os, urllib
from urlparse import urlparse

# Options by default
targetPath = "." # Current directory
username = "gaoyu"
password = "111111"
url = u"svn://221.239.81.82/surClient20120705/trunk/SurDoc/1源代码"

revision_min = pysvn.Revision( pysvn.opt_revision_kind.number, 0 )
revision_max = pysvn.Revision( pysvn.opt_revision_kind.head )
hasRevision = False
# test unicode and str
#a = u'高'
#print a
#b = '高'
#print b
#a = b
#c = a + b
#print a.decode('utf8')

# 注意修改用户名和密码是必须先添加控制参数，再按顺序添加url 和 本地路径
try:
    optlist, args = getopt.getopt (sys.argv[1:], "r:u:p:",
                                   ["revision=", "username=", "password="])
    if len(args) == 1 or len(args) == 2:
        url = args[0]
        if len(args) == 2:
            targetPath = args[1]
    elif url != "":
        pass
    else:
        raise Exception ("Input URL [targetPath]")
    for option, value in optlist:
        if option == "--username" or option == "-u":
            username = value            
        elif option == "--password" or option == "-p":
            password = value
        elif option == "--revision" or option == "-r":
            revision = value
            if string.find(value, ":") >= 0:
                (revision_min0, revision_max0) = string.split(value, ":")
                revision_min = pysvn.Revision( pysvn.opt_revision_kind.number, int(revision_min0) )
                if revision_max0 != "HEAD":
                    revision_max = pysvn.Revision( pysvn.opt_revision_kind.number, int(revision_max0) )
                    if int(revision_max0) <= int(revision_min0):
                        print revision_max,revision_min
                        raise Exception ("revision_max <= revision_min")
                hasRevision = True
            else:
                raise Exception ("Please Input revision range " + str(option))
        else:
            raise Exception ("Unknown option " + str(option))
            
    if hasRevision == False:
        raise Exception ("Please Input Revision Range -r min:max")

    urlObject = urlparse(url)
    if urlObject.scheme == 'http' or urlObject.scheme == 'https':
        url = urlObject.scheme+"://"+urlObject.netloc+urllib.quote(urlObject.path.decode(sys.stdin.encoding).encode('utf8'))
    else:
        if not isinstance(url, unicode):            #如果不是unicode 则转换为unicode，因为一下接口使用unicode编码， 可以先用type看看类型
            url = unicode(url, sys.stdin.encoding)  # 如果从控制台输入 需要从控制台的编码转换为unicode编码
    #print sys.stdin.encoding                       #当前控制台编码
        
    if not url.endswith("/"):
        url = url + "/"        
        
except getopt.error, reason:
    raise Exception ("Usage: " + sys.argv[0] + ": " + str(reason))
    
    
def get_login( realm, user, may_save ):
    return True, username, password, False
   
print username+password+url+targetPath

client = pysvn.Client()
if username != "" and password != "":
    client.callback_get_login = get_login

summary = client.diff_summarize(url, revision_min, url, revision_max)
#print summary
for changed in summary:
    #print type(changed) # <type 'instance'>
    #path, summarize_kind, node_kind, prop_changed
    #for key in changed.iterkeys():
    #    print key 
    #print "-----", changed['summarize_kind'], changed['prop_changed'], changed['node_kind'], changed['path'].encode('utf8')
    if pysvn.diff_summarize_kind.delete == changed['summarize_kind']:
      fullPath = targetPath+"/"+changed['path']   
      if os.path.exists(fullPath):
        os.remove(fullPath)

    if pysvn.diff_summarize_kind.added == changed['summarize_kind'] or pysvn.diff_summarize_kind.modified == changed['summarize_kind']:
        print changed['summarize_kind'], changed['path']
        if changed['node_kind'] == pysvn.node_kind.file:
            
            #uniPath = changed['path'].decode('utf8').encode()   #变动文件相对目录 Source/SurDoc/SurDoc/Advanced/CLS_DlgBackupSet.cpp (root 为上级目录)
            #print url #输入路径 加上 '/',拼成完整网络路径，cat获得文件内容
            #print type(urllib.quote(changed['path'].encode('utf8')))   # 不知何用  为str 应使用 中文尝试此接口
            #ll = url+urllib.quote(changed['path'].encode('utf8'))
            #print type(ll)                                             # ll 为unicode 看了上面的测试=》 如果在同步的相对目录中有中文则cat文件失败 =》unicode + str
            file_text = client.cat(url+urllib.quote(changed['path'].encode('utf8')), revision_max)
            
            fullPath = targetPath+"/"+changed['path']    #本地相对文件路径./Source/SurDoc/SurDoc/Advanced/CLS_DlgBackupSet.cpp
            dirPath = fullPath[0:fullPath.rfind("/")]    #本地相对文件目录./Source/SurDoc/SurDoc/Advanced
            #print fullPath
            #print dirPath
            if not os.path.exists(dirPath):
                os.makedirs(dirPath) # 迭代创建目录
                        
            f = open(fullPath,'wb')
            f.write(file_text)
            f.close
        elif changed['node_kind'] == pysvn.node_kind.dir:
            fullPath = targetPath+"/"+changed['path']    #本地相对文件路径./Source/SurDoc/SurDoc/Advanced/CLS_DlgBackupSet.cpp
            if not os.path.exists(fullPath):
                os.makedirs(fullPath) # 迭代创建目录
