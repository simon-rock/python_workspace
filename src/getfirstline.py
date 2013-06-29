#coding=utf-8
#值显示文件的第一行
from optparse import OptionParser, SUPPRESS_HELP
import os
def get_options(args=None):
    """Parse command line options and parameters."""

    parser = OptionParser(add_help_option=False, usage='%prog <arg> [option]', description="")
    global HELP
    HELP = parser.format_help().strip()
    options, args = parser.parse_args(args)
    print HELP
    return options, args
    
def main(argv = None):
    (options, argv) = get_options(argv)
    print argv
    for f in argv:
        path, filename = os.path.split(f)
        # 安行读取文件
        file_obj = open(f)
        l = file_obj.readline()
        print "[%s] %s" %(filename, l)
        file_obj.close()
if __name__ == "__main__":
    main()
