#!/usr/bin/env python
#coding=utf-8
#中文
import os
import sys
import platform
if platform.system() == "Windows":
    import win32con, win32api
else:
    import stat
filenamenum = 0

def iswindows():
    sysstr = platform.system()
    return sysstr == "Windows"


# windows 下 修改文件属性
def make_writable(path):
    if os.path.exists(path):
        if iswindows():
            win32api.SetFileAttributes(path, win32con.FILE_ATTRIBUTE_NORMAL)
        else:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)     # linux

# 遍历文件深度 优先
def traverse_file(path):
    "delete all folers and files"
    if os.path.isfile(path):
        try:
            #处理文件
            filepath, ext = os.path.splitext(path)
            dirpath, filename = os.path.split(path)
            #print "%s [%s][%s]" % (dirpath, filename, ext)
            newpath = "%s\index.html" % dirpath
            make_writable(path)
            clear_file = open(path, 'w+')
            clear_file.flush()
            clear_file.close()
            os.rename(path, newpath)
            os.remove(newpath)
        except:
            print "error [%s]" % path
            pass
    elif os.path.isdir(path):
        #处理文件夹
        for item in os.listdir(path):
            itemsrc = os.path.join(path, item)
            global filenamenum
            filenamenum += 1
            newpath = "%s/%d" % (path, filenamenum)
            os.rename(itemsrc, newpath)
            print newpath,"---->",itemsrc
            traverse_file(newpath)

        try:
            dirpath, filename = os.path.split(path)
            newpath = "%s/root" % dirpath
            make_writable(path)
            print "remove", path
            pause  = raw_input()
            os.rename(path, newpath)
            os.rmdir(newpath)
            pause = raw_input()
        except:
            print "error [%s][%s]" % (path, newpath)
            pass

if __name__ == "__main__":
    #print sys.path
    dirpath = "%s/%s" % (os.getcwd(), "L")
    #print os.path.realpath(file)
    if os.path.exists(dirpath):
        traverse_file(dirpath)
        if iswindows():
            os.mkdir(dirpath)
        else:
            os.mkdir(dirpath, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    else:
        print "no path"
