#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import os
import shutil
import os
import glob
import sys
from stat import *

from optparse import OptionParser, SUPPRESS_HELP
# for mail
#modules for mail notification
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders
from socket import gethostname

#添加系统目录，以当前文件目录为基础
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

#创建目录
def create_directories(directory_list):
    """Creates each directory in the list if it does not exist."""
    for directory in directory_list:
        if not os.path.exists(directory):
            printv('makedirs: %s' % directory)
            os.makedirs(directory)

#重命名目录，错误会抛出异常
def rename_directories(directory_list):
    """Renames each directory in the list by appending a timestamp."""
    timestamp = time.strftime('%y%m%d-%H%M')
    for directory in directory_list:
        if os.path.exists(directory):
            saved_dir = '%s.%s' % (directory.rstrip(os.sep), timestamp)
            try:
                os.rename(directory, saved_dir)
            except OSError:
                printv('ERROR: Cannot rename %s.' % directory)
                printv('Make sure all files in the directory are closed.')
                raise
#清空一个目录
def empty_dir(path):
    """Delete all files in the given directory."""
    for filename in os.listdir(path):
        del_path = os.path.join(path, filename)
        if os.path.isfile(del_path):
            try:
                os.remove(del_path)
            except Exception, e:
                printv('empty_dir, exception:', e)
                raise
#时间戳
def timestamp():
    timestamp = time.strftime('%y%m%d-%H%M%S')
    print timestamp,
#时间字符串
def time_str():
    tm = time.localtime()
    tm_str = '%d%02d%02d' % (tm[0:3])
    return tm_str

#解压文件到目录，先通过实践戳判断版本，会刷新版本
def extract_gz(src_tar, dest_gz, dest_path, verbose):
    """Extracts the SIF GZ file from its tar to the destination directory.
    NOTE: This stats the tar file itself, not the gz file inside the tar. Is
    that the intention?
    """

    if verbose:
        printv('\nextract_gz, src_tar: %s' % src_tar)
        printv('extract_gz, dest_gz:   %s' % dest_gz)
        printv('extract_gz, dest_path: %s' % dest_path)

    same_file = False
    tar_stat = os.stat(src_tar)
    dest_file = os.path.join(dest_path, dest_gz)
    if os.path.exists(dest_file):
        src_modtime = tar_stat.st_mtime
        dest_stat = os.stat(dest_file)
        dest_modtime  = dest_stat.st_mtime
        if verbose:
            printv('src mtime:  %s' % src_modtime)
            printv('dest mtime: %s' % dest_modtime)
        if src_modtime == dest_modtime:  # Same file, do not extract.
            same_file = True

    if verbose:
        if same_file:
            printv('%s matches src, not copying' % dest_gz)
        else:
            printv('%s does not match src, copying' % dest_gz)

    if not same_file:
        tar_file = tarfile.open(src_tar)
        tar_file.extract(dest_gz, dest_path)
        # Change the last access and last modification time for local GDF.
        # Doing this will eliminate recopying existing data for subsequent runs.
        try:
            os.utime(dest_file, (tar_stat.st_atime, tar_stat.st_mtime))
        except:
            printv('WARNING: Could not set mtime for %s' % dest_file)

#异常使用
class TarFileNotFound(Exception):
    pass
def get_tar(cfg, key):
    if True:
        return
    raise TarFileNotFound('No tar file found for %s (%s)' % (key, cfg.Period))

def test():
    #rename dir
    os.rename(directory, saved_dir)
    #remove dir
    shutil.rmtree(directory)
    print "ok"
    
if __name__ == "__main__":
    test()

