#!/usr/bin/env python
#coding: utf-8
import commands
import os
import sys
#from remotecmd import action
from optparse import OptionParser

PARAM_ERROR      = -1
CREATE_OSD_ERROR = -2
GET_OSDID_ERROR  = -3
UPDATA_ERROR     = -4

def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    parser.add_option('', '--uuid', action="store", dest='task_uuid', default="", help='')
    parser.add_option('', '--host', action="store", dest='host', default="", help='')
    parser.add_option('', '--data_dev', action="store", dest='data_dev', default="", help='')
    parser.add_option('', '--juuid', action="store", dest='juuid', default="", help='journal uuid')
    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)

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
        update_status(options.task_uuid, "", options.juuid, PARAM_ERROR)
        return PARAM_ERROR
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
    s = 0
    os.chdir(last_dir)
    if s != 0:
        print s,"---",o
        update_status(task_uuid, "", juuid, CREATE_OSD_ERROR)
        return CREATE_OSD_ERROR

    # get osd id
    cmd = "ceph-disk list | grep " + data_dev + "1 | awk -F \"osd.\" '{print $2}'"
    print cmd
    s,o = commands.getstatusoutput(cmd)
    print s,"---",o
    if s != 0 or len(o) == 0:
        print s,"---",o
        update_status(task_uuid, "", juuid, GET_OSDID_ERROR)
        return GET_OSDID_ERROR
    osdid = o.replace("\n", "") 
    return update_status(task_uuid, osdid, juuid, 0)

def update_status(task_uuid, osdid, juuid, stat ):
    cmd = "/usr/bin/updateCephOsd --osd-uuid " + task_uuid

    if stat == 0 and osdid != "":
        cmd += " --status active --osd-id osd."+ osdid
    elif stat == -1: 
        cmd += " --status param_error"
    elif stat == -2:
        cmd += " --status create_osd_error"
    elif stat == -3:
        cmd += " --status get_osdid_error"
    else: 
        cmd += " --status unknow_error"
    cmd += " --journal-uuid "+juuid if (juuid!="") else ""
    print cmd
    s,o = commands.getstatusoutput(cmd)
    s = 0
    if  s != 0:
        print s,"---",o
        return UPDATA_ERROR
    return 0
if __name__ == "__main__":
    main()
