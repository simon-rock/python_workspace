#coding: utf-8
import os, string
from os.path import join, getsize  
from optparse import OptionParser, SUPPRESS_HELP
import md5
import io
all_dici = "A1 BB C1 C4 CA E1 E2 E3 E4 E5 E6 E7 F1 F2 F3 F4 F5 F6 F7 G1 G2 G3 G4 G5 G6 G7 G8 H1 H2 H4 H5 H6 I1 I2 I3 I4 I5 K1 K2 K3 K4 K5 K6 K7 K8 K9 LU N1 NL S1 S2 S3 S4 SP SQ SU SV"

all_dici_list = all_dici.split(" ")
#参数获得
def get_options(args=None):
    """Parse command line options and parameters."""

    parser = OptionParser(add_help_option=False, usage='%prog <arg> [option]', description="")
    parser.add_option('-s', action='store', type='string', dest='folder1', help='folder1')
    parser.add_option('-t', action='store', type='string', dest='folder2', help='folder2')
    parser.add_option('-n', action='store', type='string', dest='name', help='diff file name')
    parser.add_option('-c', action='store_true', dest='cal_file', default=False, help='directly calculate')
    parser.add_option('-h', '--help', dest='help', action='store_true', default=False, help="show this doc")
    global HELP
    HELP = parser.format_help().strip()
    options, args = parser.parse_args(args)
    #print HELP
    return options, args

def get_raw_size(dir, raw_name, recursion, dici_size):
    files = os.listdir(dir)
    for name in files:
        fullname=os.path.join(dir,name)
        #print fullname
        if(os.path.isdir(fullname) & recursion):
            get_raw_size(fullname,raw_name,recursion, dici_size)
        else:
            if not cmp(name, raw_name):
                folder_list = fullname.split(os.path.sep)
                for dic in folder_list:
                    if dic in all_dici_list:
                        #use md5 of file
                        #key = md5.new()
                        f = open(fullname, "rb")
                        #key.update(f.read())
                        strsize = getsize(fullname)
                        strdigest = md5.new(f.read()).hexdigest()
                        print dic, " ==> ", strsize, strdigest, fullname#digest()
                        f.close()
                        # use file size
                        #print dic, " ==> ",getsize(fullname)
                        total = str(strsize) + "-" + strdigest
                        dici_size[dic] = total
                        
def main(argv = None):
    (options, argv) = get_options(argv)
    global OPTION
    OPTION = options
    if OPTION.help:
        print HELP
        return
    if OPTION.cal_file:
        test_md5(OPTION.name)
        return
    #print OPTION.folder1
    #print OPTION.folder2
    dici_size1 = {}
    dici_size2 = {}
    print "process -- ", OPTION.folder1
    get_raw_size(OPTION.folder1, OPTION.name, 1, dici_size1)
    print "process -- ", OPTION.folder2
    get_raw_size(OPTION.folder2, OPTION.name, 1, dici_size2)
    print "-----"
    #for k in dici_size2.iterkeys():
    #    print k, "\t =>", dici_size2[k]
    for k in dici_size2.iterkeys():
        if not dici_size1.has_key(k):
            print "dici_size1 not this ", k
        elif dici_size1[k] != dici_size2[k]:
            print "dici_size1", k, "\t =>", dici_size1[k]
            print "dici_size2", k, "\t =>", dici_size2[k]

def test_md5(file_path):
    print "start"
    #f = open(file_path, "rb")
    #strdigest = md5.new(f.read()).hexdigest()
    strsize = getsize(file_path)
    f = io.FileIO(file_path, 'r')
    bytes = f.read(1024)
    digest = md5.new()
    while(bytes != b''):
        digest.update(bytes)
        bytes = f.read(1024)
    f.close()
    strdigest = digest.hexdigest()
    print strsize, strdigest, file_path
    print "end"
if __name__ == "__main__":
    main()

