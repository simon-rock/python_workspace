#coding: utf-8
import os
import pysvn
import shutil
#操作本地副本

url = u'http://20100522-1612:8080/svn/test_for_auto_sync_src'         #svn url
svn_path = u"D:/auto_sync/auto_sync_src"
tmp_path = u'D:/svn_tmp2'
def checkout():
    client = pysvn.Client()
    client.checkout(url, tmp_path, revision=pysvn.Revision(pysvn.opt_revision_kind.number, 4))

def update():
    client = pysvn.Client()
    client.update(tmp_path)

def add(file):
#    try:
        path1 = "D:/auto_sync/auto_sync_src/3"
        path2 = "D:/auto_sync/auto_sync_src/3/4/123.txt"
        path3 = "sdfsadf"
        print path3.find(path1)
        client = pysvn.Client()
        client.exception_style = 1
        try:
            client.add("D:/auto_sync/auto_sync_src/8/11.txt")
        except pysvn.ClientError, e:
            #print str(e)
            #print e.args
            if len(e.args[1]) == 1 and e.args[1][0][1] == 150002:
                print e.args[0]
            else:
                raise
#            for message, code in e.args[1]:
#                print 'Code:',code,'Message:',message
        print "continue"
            
        #changelist = []
#        changelist.add("b")
        #changelist.add()
        #client.remove('D:/svn_tmp2/1111.txt')
        #client.checkin(["D:/svn_tmp2/1111.txt"], "test remove")
#    except pysvn.ClientError, e:
#        print str(e)
#        print e.args
#        pass
#        print "error"
def main():
    #checkout()
    #update()
    add("asd")
if __name__ == '__main__':
    main()
    #shutil.rmtree("D:\svn_tmp")
        
