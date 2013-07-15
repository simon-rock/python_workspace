#! /usr/bin/env python
#coding=utf-8
import pysvn
import datetime
import sys
import time
username = "gaoyu"
password = "111111"

def get_login( realm, user, may_save ):
    return True, username, password, False

#root_path = r"E:\surdoc_svn\SurDoc\1"
root_path = r"E:/code/svn/SurDoc/1源代码"
root_folder = u"1源代码"
client = pysvn.Client()
entry = client.info(root_path)
print "-----info-----"
print r'SVNpath:',entry.url.encode("utf8")
print r'lastest version:',entry.commit_revision.number
print r'commit user:',entry.commit_author
print r'update:', datetime.datetime.fromtimestamp(entry.commit_time)
print "-----info2-----"
print entry
pause = raw_input()
entry2 = client.info2(root_path, revision=pysvn.Revision( pysvn.opt_revision_kind.head ),peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ), recurse = False)
print entry2
for name, o in entry2:
    print type(name), type(root_folder)
    print name.decode('utf8'), root_folder
    if cmp(name.decode('utf8'), root_folder):
        print name, o
        for k in o.iterkeys():
            print k
        print o.rev.number
        
print len(entry2)    
pause = raw_input()
print "---------log"
client2 = pysvn.Client()
revision_start = pysvn.Revision(pysvn.opt_revision_kind.head)
#LogList = client2.log("http://20100522-1612:8080/svn/test_for_auto_sync_src",revision_start,limit=10)
LogList = client2.log("http://20100522-1612:8080/svn/test_for_auto_sync_src",revision_start,limit=0)
for l in LogList:
    print l
    #for k in l.iterkeys():
    #    print k
    print "---------------", l['revision'].number
    print time.strftime("%Y-%m-%d", time.localtime(l.date))
    print l.author
    print l.message
    print l.has_children
    print l.revprops
    print l.revision
    print l.changed_paths
print "------------"
client_log = pysvn.Client()
list_of_revprop_names =[]
#svn://221.239.81.82/surClient20120705/trunk/SurDoc/1源代码
#"http://20100522-1612:8080/svn/test_for_auto_sync_src"
#pysvn.opt_revision_kind.head
#注意这个选项会改变返回日志的类型discover_changed_paths=False  => PysvnLog, True  = >PysvnLogChangedPath
#及变动的文件和提交的信息不能同时获得
log_messages = \
client.log( u"http://20100522-1612:8080/svn/test_for_auto_sync_src",\
     revision_start=pysvn.Revision( pysvn.opt_revision_kind.head),\
     revision_end=pysvn.Revision( pysvn.opt_revision_kind.number, 0 ),\
     discover_changed_paths=False,\
     strict_node_history=True,\
     limit=1,\
     peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ),\
     include_merged_revisions=False,\
     revprops=list_of_revprop_names )\

for message in log_messages:
    #for k in message.iterkeys():  # has_children,revprops,changed_paths,revision
    #    print k
    print "---------------", message['revision'].number
    #print message.message  #error !!!!!!
    #for k in message['revision'].iterkeys():
    #    print k
    print message['has_children']
    #print message['author']
    print message['revprops']
    print message['changed_paths']
    for i in message['changed_paths']:
        for kk in i.iterkeys():
            print kk
        print i['action'], i['path']  # A D M
        #type(i['copyfrom_path'])
        #print i['copyfrom_path'].decode('utf8')
        #print i['copyfrom_revision']
        #print i.message
        print "next"
    #print message.has_children
    #print message.changed_paths
    #print message.revision
print list_of_revprop_names
print "new"
print sys.stdin.encoding
