#encoding: utf-8
#说明 指定白名单生成的PNG 目录，指定sar的源目录，将白名单的sar源文件拷贝到指定目录、
import sys
import shutil
import os
from optparse import OptionParser, SUPPRESS_HELP
from stat import *
def get_options(args=None):
    """Parse command line options and parameters."""

    parser = OptionParser(add_help_option=False, usage='%prog <arg> [option]', description="")
    parser.add_option('-w', '--white_folder', action='store', type='string', default="M:/Users/Summer fu/13Q1-whitelist", dest='white_folder', help='whitelist folder')
    parser.add_option('-s', '--sar_folder', action='store', type='string', default="D:/work/Enhanced/SAR_samsung/sar/SAR", dest='sar_folder', help='sar folder')
    parser.add_option('-d', action='store', type='string', default="d:/test", dest='out_folder', help='out folder')
    parser.add_option('-h', '--help', dest='help', action='store_true', default=False, help="show this doc")
    global HELP
    HELP = parser.format_help().strip()
    options, args = parser.parse_args(args)
    #print HELP
    return options, args

def listfiles(dir,wildcard,recursion, white_list):
    exts = wildcard.split(" ")
    files = os.listdir(dir)
    for name in files:
        fullname=os.path.join(dir,name)
        if(os.path.isdir(fullname) & recursion):
            listfiles(fullname,wildcard,recursion, white_list)
        else:
            for ext in exts:
                if(name.endswith(ext)):
                    ports = name.split("_SIGN_")
                        #print ports[2]
                    white_list.add(ports[0]+".svg")
                    #file.write(name + "\n")
                    break

def make_dir(path, clean=False):
    '''make directory'''
    if not os.path.exists(path):
        os.makedirs(path)
    elif clean:
        shutil.rmtree(path)
        os.makedirs(path)

# 添加写标志
def make_writable(path):
    if os.path.exists(path):
        os.chmod(path, S_IWRITE)

def copy_file(src, dest_path, dest_file=None):
    if not dest_file:
        path, name = os.path.split(src)  #分割路径和文件名
        dest_file = name
    dest = os.path.join(dest_path, dest_file)
    make_writable(dest)
    if not os.path.exists(src):
        print '%s not exist' % (src)
        return
    try:
        shutil.copy(src, dest)
    except Exception, e:
        print 'copy_file, exception:', e
        raise

    #make_writable(dest)
    #os.rename(dst_name, "final_name")


def selectfilesfromfolder(dir, out, recursion, white_list):
    files = os.listdir(dir)
    for name in files:
        fullname=os.path.join(dir,name)
        if(os.path.isdir(fullname) & recursion):
            selectfilesfromfolder(fullname, out, recursion, white_list)
        else:
            if name in white_list:
                copy_file(fullname, out, name)
def main(argv = None):
    (options, argv) = get_options(argv)
    global OPTION
    OPTION = options
    if OPTION.help:
        print HELP
        return
    white_list = set()
    make_dir(OPTION.out_folder)
    listfiles(OPTION.white_folder, "PNG", 1, white_list)
    #print len(white_list)
    selectfilesfromfolder(OPTION.sar_folder, OPTION.out_folder, 1, white_list)
    
if __name__ == "__main__":
    main()

