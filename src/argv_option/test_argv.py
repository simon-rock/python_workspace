from optparse import OptionParser

MSG_USAGE = "myprog [-f <filename>][-s <xyz>]arg1[,arg2...]"

def get_options(args=None):
    optParser = OptionParser(MSG_USAGE)
    optParser.add_option("-f",
                         "--file",
                         action = "store",
                         default = "defaultfile",
                         type = "string",
                         dest = "filename")
    optParser.add_option("-s",
                         "--someopt",
                         type = "string",
                         default = "defaultsomeopt",
                         dest = "someopt")
    global HELP
    HELP = optParser.format_help().strip()

    fakeArgs = ['-f', 'thefile.txt', '-s', 'xyz', 'arg1', 'arg2', 'arge']
    options, args = optParser.parse_args(args)
    print options.filename
    print options.someopt
    print args
    print HELP
    return options, args
    
def main(argv=None):
    (options, argv) = get_options(argv)
    global OPTION
    OPTION = options
    
if __name__ == '__main__':
    main()

