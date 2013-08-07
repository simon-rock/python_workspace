#!/usr/bin/env python
#coding=utf-8
#遍历文件夹 处理
import os
import sys
import win32con, win32api
filenamenum = 0

# windows 下 修改文件属性
def make_writable(path):
    if os.path.exists(path):
        #os.chmod(path, S_IWRITE)     # linux
        win32api.SetFileAttributes(path, win32con.FILE_ATTRIBUTE_NORMAL)

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
            newpath = "%s\\%d" % (path, filenamenum)
            os.rename(itemsrc, newpath)
            print newpath,"---->",itemsrc
            traverse_file(newpath)

        try:
            dirpath, filename = os.path.split(path)
            newpath = "%s\\root" % dirpath
            make_writable(path)
            os.rename(path, newpath)
            os.rmdir(newpath)
        except:
            print "error [%s][%s]" % (path, newpath)
            pass

if __name__ == "__main__":
    #dirname = r'P:\12\L'
    #print sys.path
    dirpath = "%s\\%s" % (os.getcwd(), "L")
    print dirpath
    #print os.path.realpath(file)
    if os.path.exists(dirpath):
        traverse_file(dirpath)
        os.mkdir(dirpath)
    else:
        print "no path"
