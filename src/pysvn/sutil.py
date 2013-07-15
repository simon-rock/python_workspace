#coding: utf-8
import os
import os.path
import shutil
#目录数
#symlinks : whether copy link
#force : whether rewrite existed file
def copytree(src, dst, symlinks=False, force = False):
    if not force:
        shutil.copytree(src, dst, symlinks)
        return
    names = os.listdir(src)
    if not os.path.isdir(dst):
        os.makedirs(dst)
        
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, force)
            else:
                if os.path.isdir(dstname):
                    os.rmdir(dstname)
                elif os.path.isfile(dstname):
                    os.remove(dstname)
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except OSError as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        print errors
        raise shutil.Error(errors)


#! /usr/bin/env python 
#coding=utf-8 
## {{{ Recipe 193736 (r1): Clean up a directory tree  
""" removeall.py:
   Clean up a directory tree from root.
   The directory need not be empty.
   The starting directory is not deleted.
   Written by: Anand B Pillai <abpillai@lycos.com> """ 
 
import sys, os 
 
ERROR_STR= """Error removing %(path)s, %(error)s """ 
 
def rmgeneric(path, __func__): 
 
    try: 
        __func__(path) 
#        print 'Removed ', path 
    except OSError, (errno, strerror): 
        print ERROR_STR % {'path' : path, 'error': strerror }
#        pause = raw_input()
             
def removeall(path): 
 
    if not os.path.isdir(path): 
        return 
     
    files=os.listdir(path) 
 
    for x in files: 
        fullpath=os.path.join(path, x) 
        if os.path.isfile(fullpath): 
            f=os.remove 
            rmgeneric(fullpath, f) 
        elif os.path.isdir(fullpath): 
            removeall(fullpath) 
            f=os.rmdir 
            rmgeneric(fullpath, f) 
## End of recipe 193736 }}} 
if __name__ == '__main__':
    #copytree('d:/py_test/test1', 'd:/py_test/test2')
    copytree('d:/py_test/test1', 'd:/py_test/test2', False, True)
