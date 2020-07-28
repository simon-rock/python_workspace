#!/usr/bin/env python
#coding: utf-8

'''
data file example:
x: osd180_5
data: min: 0.888064 max: 1.09864 ex: 546.132

==
min: max: ex: is label
osd180_5 is x
0.888064 is y
'''



import os
from optparse import OptionParser
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
g_debug = False

xpoints = []
labels = set()
ypoints = {}

def skip_label(str):
    if str == "ex:":
        return True
    return False
 
def get_info(line):
    if line.startswith("x:"):
        xpoints.append(line.split(" ")[1])
    if line.startswith("data:"):
        d = line.split(" ")
        curr_label = ""
        for i in d:
            if i.startswith("data:"):
                continue
            if i.endswith(":"):
                if skip_label(i):
                    curr_label = ""
                    continue
                curr_label = i
                labels.add(i)
                if not ypoints.has_key(i):
                    ypoints[i] = []
            else:
                if curr_label != "":
                    ypoints[curr_label].append(float(i))
        '''        
        labels.add(d[1])
        labels.add(d[3])
        labels.add(d[5])

        if not ypoints.has_key(d[1]):
            ypoints[d[1]] = []
        if not ypoints.has_key(d[3]):
            ypoints[d[3]] = []
        if not ypoints.has_key(d[5]):
            ypoints[d[5]] = []
        ypoints[d[1]].append(float(d[2]))
        ypoints[d[3]].append(float(d[4]))
        ypoints[d[5]].append(float(d[6]))
        '''

def format_fn(tick_val, tick_pos):
    if int(tick_val) < len(xpoints):
        return xpoints[int(tick_val)]
    else:
        return ''

def draw():
    print "ok"
    llabels = list(labels)
    length = len(xpoints)
    print llabels
    for item in llabels:
        plt.plot(range(length), ypoints[item], label=item)
    '''
    plt.plot(range(length), ypoints[llabels[0]], label=llabels[0])
    plt.plot(range(length), ypoints[llabels[1]], label=llabels[1])
    plt.plot(range(length), ypoints[llabels[2]], label=llabels[2])
    '''
#    fig = plt.figure(figsize=(8,6))
#    ax = fig.add_subplot(111) 
    ax=plt.gca()
    ax.xaxis.set_major_formatter(FuncFormatter(format_fn))
    plt.grid()
    plt.legend()
    plt.title("request ")
    plt.show()
    
def process(log_path):
    global TASKS
    fp = open(log_path, 'r')
    #out_path = os.path.join(out, "out")
    #print out_path
    for line in fp.readlines():
        get_info(line)
    fp.close()
    draw()
    #dump to out file
    #f = file(out_path, "w")
    #p.dump(TASKS, f)
    #f.close
                                                    
def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    #parser.add_option('-d', '--outputdir',action='store', dest='outdir', default='.', help='*.BIN files output directory')
    #parser.add_option('-t', '--TT', action="store_true", dest='tt_nt', default=False, help='process TT landmark, default NT')
    #parser.add_option('-p', '--processconfig', action="store_true", dest='processconfig', default=False, help='only process landmark_table')
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    #parser.add_option('-a', '--analyzedfile', action="store_true", dest='analyzed', default=False, help='open a analyzed file')
    #parser.add_option('-o', '--outnanlyzed',action='store', dest='outdir', default='.', help='dir of analyzed file')
    #parser.add_option('-c', '--threshold',action='store', dest='cost', default='0', help='microseconds(us), only analy the event which cost over the threshold')
    #parser.add_option('-p', '--print', action="store_true", dest='print_only', default=False, help='print only through the filter')
    # for real time
    #parser.add_option('-r', '--realtime', action="store_true", dest='realtime', default=False, help='realtime analy')
    #parser.add_option('-m', '--onlymain', action="store_true", dest='onlymain', default=False, help='only analy main req')
    #parser.add_option('-f', '--filter_event', action="store", dest='event', default="all", help='event name')
    #parser.add_option('-t', '--print_event', action="store", dest='pevent', default="all", help='event name')
    #parser.add_option('-d', '--debugmode', action="store_true", dest='debug_mode', default=False, help='debug mode(default false)')
    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)
    
    #if not options.realtime and  len(argvs) < 1 and not options.version:
    #    parser.error("Please specify the directory of the file to be processed.")
    return options, argvs

def main(args=None):
    global options
    global argvs
    global g_debug
    (options, argvs) = get_options(args)
    print argvs[0]
    process(argvs[0])

if __name__ == "__main__":
        main()
