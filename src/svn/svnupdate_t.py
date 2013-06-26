#encoding: utf-8
import time,os,sys,svnconfig

dist=svnconfig.setting['dist']
#os.chdir(svnconfig.setting['svn'])

def checkout():
    svnconfig.setting['dist']=dist+time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime())
    cmd='svn export %(url)s %(dist)s --username %(user)s --password %(pwd)s'%svnconfig.setting
    print "execute %s"%cmd
    #print os.popen(cmd).read()
    return os.system(cmd)


if __name__ == "__main__":
    print sys.path
    print os.path
    while True:
        ret=checkout()
        if(ret==0):
            print 'check out success'
        else:
            print 'check out fail'
        time.sleep(svnconfig.setting['interval'])

