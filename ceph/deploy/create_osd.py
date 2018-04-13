#!/usr/bin/env python
#coding: utf-8
import commands
import os
import sys
from remotecmd import action
from optparse import OptionParser

PARAM_ERROR      = -1
CREATE_OSD_ERROR = -2 
GET_OSDID_ERROR  = -3
UPDATA_ERROR     = -4

def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    # print osdmap chenge list
    parser.add_option('', '--uuid', action="store", dest='task_uuid', default="", help='')
    parser.add_option('', '--host', action="store", dest='host', default="", help='')
    parser.add_option('', '--data_dev', action="store", dest='data_dev', default="", help='')
    parser.add_option('', '--juuid', action="store", dest='juuid', default="", help='journal uuid')
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
    print argvs
    print options
    if options.task_uuid == "" or options.host == ""or options.data_dev == "":
        print "need <uuid> <host> <data_dev>"
        return PARAM_ERROR
    username = "root"
    task_uuid = options.task_uuid
    host = options.host
    data_dev = options.data_dev
    juuid = options.juuid
    journal = ""
    if options.juuid != "":
        journal = ":/dev/disk/by-partuuid/"+juuid

    last_dir = os.getcwd()

    # create osd
    os.chdir('/etc/ceph')
    cmd = "ceph-deploy osd create --fs-type xfs " + host + ":" + data_dev+journal
    print cmd
    s,o = commands.getstatusoutput(cmd)
    os.chdir(last_dir)
    if s != 0:
        print s,"---",o
        return CREATE_OSD_ERROR

    # get osd id
    cmd = "ceph-disk list | grep " + data_dev + "1 | awk -F \"osd.\" '{print $2}'"
    conn = action(host,username,cmd)
    ret, el, ol = conn.ssh_connect()
    print "--",cmd,"-----",ret, el, ol, len(ol)
    if ret < 0 or len(ol) != 1:
        return GET_OSDID_ERROR

    # update info
    osdid = ol[0].replace("\n", "")
    cmd = "/usr/bin/updateCephOsd --osd-uuid " + task_uuid + " --osd-id osd."+ osdid + " --status active --journal-uuid "+juuid
    print cmd
    s,o = commands.getstatusoutput(cmd)
    if  s != 0:
        print s,"---",o
        return UPDATA_ERROR
    return 0

if __name__ == "__main__":
    main()
