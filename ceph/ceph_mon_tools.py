#!/usr/bin/env python
#coding: utf-8
#
# ceph daemon osd.17 config  set debug_optracker 5
# so, you can filter the sp. log using tailf osd.17.log | ananly_ceph_log.py -r [-f event or all] [-t print_event or all] [-c cost or 0]
#
#
import re
import string
import os
import datetime
import time
import sys
import cPickle as p
import commands
from optparse import OptionParser
import signal

# global define
version = u"0.1"
ceph_monstore_tool = u"/root/workspace/ceph-monstore-tool"
mondb_path = u"/var/lib/ceph/mon/mon.a/"
#
is_sigint_up = False
TASKS = {}
EVENT_STAT = {}
def sigint_handler(signum, frame):
    global is_sigint_up
    global EVENT_STAT
    is_sigint_up = True
    print "catch interrupt signal!"
    time.sleep(1)
    print ("%-55s "%("key")), ("%-13s "%("avg_cost")),("%-13s "%("max")),("%-13s "%("min")),("%-13s "%("total_count"))
    for key, val in EVENT_STAT.items():
        print ("%-55s "%(key)), val["avg_cost"], val["max"], val["min"],  val["total_count"]

# get all the 
def list_keys():
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "dump-keys | awk '{print $1}' | uniq -c" 
    out = commands.getoutput(cmd)
    print out

# get version of all the tables
def show_versions():
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "dump-keys | awk '{print $1}' | uniq" 
    out = commands.getoutput(cmd)
    for data in out.split():
        print "--", data
        show_version(data)
def show_version(map_type):
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "show-versions -- --map-type " + map_type 
    out = commands.getoutput(cmd)
    print out
    
def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    parser.add_option('-k', '--listkays', action="store_true", dest='listkeys', default=False, help='list all the keys')
    parser.add_option('-s', '--showversions', action="store_true", dest='showversions', default=False, help='show the version of all the map type')
    #parser.add_option('-o', '--outnanlyzed',action='store', dest='outdir', default='.', help='dir of analyzed file')
    #parser.add_option('-c', '--threshold',action='store', dest='cost', default='0', help='microseconds, only analy the event which cost over the threshold')
    #parser.add_option('-p', '--print', action="store_true", dest='print_only', default=False, help='print only through the filter')
    # for real time
    #parser.add_option('-r', '--realtime', action="store_true", dest='realtime', default=False, help='realtime analy')
    #parser.add_option('-f', '--filter_event', action="store", dest='event', default="all", help='event name')
    #parser.add_option('-t', '--print_event', action="store", dest='pevent', default="all", help='event name')

    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)

    #if not options.realtime and  len(argvs) < 1 and not options.version:
    #    parser.error("Please specify the directory of the file to be processed.")
    return options, argvs

def main(args=None):
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    global options
    global argvs
    (options, argvs) = get_options(args)
    print argvs
    print options
    if options.version:
        print version
        return
    if options.listkeys:
        list_keys()
        
    if options.showversions:
        show_versions()
    print "process"
if __name__ == "__main__":
    main()
