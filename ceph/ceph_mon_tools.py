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
import json

# global define
version = u"0.2"
cmd_path = u"/root/workspace/"
ceph_monstore_tool = cmd_path + u"ceph-monstore-tool"
ceph_kvstore_tool = cmd_path + u"ceph-kvstore-tool"
ceph_dencoder = u"/usr/bin/ceph-dencoder"
mondb_path = u"/var/lib/ceph/mon/mon.a/"
redc = "\033[1;31;40m"
defaultc="\033[0m"
ceph_func = {}
key_list = "auth logm mdsmap monitor monmap osd_metadata osdmap paxos pgmap pgmap_meta pgmap_osd pgmap_pg"
g_debug = False
#
is_sigint_up = False
TASKS = {}
EVENT_STAT = {}
def debug_print(str):
    global g_debug
    if g_debug:
        print "debug: ", str
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
    debug_print(cmd)
    out = commands.getoutput(cmd)
    print out

# get version of all the tables
def show_versions():
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "dump-keys | awk '{print $1}' | uniq"
    debug_print(cmd)
    #out = commands.getoutput(cmd)
    out = key_list
    for data in out.split():
        print "--", data
        ceph_func["show_version"](data)
        
# show the first committed and last committed of the map type
def _show_version(map_type):
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "show-versions -- --map-type " + map_type
    debug_print(cmd)
    out = commands.getoutput(cmd)
    print out
def _show_version_0945(map_type):
    #10.2 usage need leveldb
    #cmd = ceph_kvstore_tool + " leveldb " + mondb_path + "store.db/ get " + map_type
    #0.945 no leveldb
    cmd = ceph_kvstore_tool + ceph_func["kvtool_cmd"] + mondb_path + "store.db/ get " + map_type
    debug_print(cmd)
    out = commands.getoutput(cmd+" first_committed out map_v")
    if out.find("not exist") ==-1:
        out = commands.getoutput("cat map_v | hexdump && rm -f map_v")
        print "first_committed\t", int(out.split()[1],16)
    else:
        print "first_committed\t-"
    out = commands.getoutput(cmd+" last_committed out map_v")
    if out.find("not exist") ==-1:
        out = commands.getoutput("cat map_v | hexdump && rm -f map_v")
        print "last_committed\t", int(out.split()[1],16)
    else:
        print "last_committed\t-"
        
def show_history(s,e):
    info_last = {}
    info_curr = {}
    first = True
    for i in range(s, e+1):
        info_curr = ceph_func["get_history"](i)
        #print info_curr
        #continue
        if first:
            first = False
            #print redc+"-----", info_curr["time_day"], "-----"+defaultc
            print make_red(info_curr["time_day"])
        else:
            _print_change(info_last, info_curr)
        info_last = info_curr

def make_red(s):
    return redc+s+defaultc
def _print_change(last, curr):
    global options
    
    if last["time_day"] != curr["time_day"] :
        #print redc+"-----", curr["time_day"], "-----"+defaultc
        print make_red(curr["time_day"])
    base = {}
    if last["max_osd"] > curr["max_osd"] :
        base = last
    else:
        base = curr
    out_t = base["time_hour"] + " " + str(base["epoch"]) + ": "
    out = ""
    for key in base.keys():
        if key in ["epoch", "fsid", "created", "modified", "flags"]:
            continue
        # pool
        if key.startswith("pool"):
            if key == "pool" and last[key] != curr[key]:
                out += "change pool " + str(last["pool"]) + "=>" + str(curr["pool"]) + " "+make_red("|")
            elif last.has_key(key) and curr.has_key(key):
                if isinstance(last[key], str) and last[key] != curr[key]:
                    out += key+":"+last[key] + "=>" + curr[key] + " "+make_red("|")
                elif isinstance(last[key], list):
                    for m in range(len(base[key])):
                        if last[key][m] != curr[key][m]:
                            o = key + ":" + last[key][m] + "=>"+curr[key][m] + " "+make_red("|")
                            out += o
        #osd
        if key.startswith("osd"):
            if last.has_key(key) and not curr.has_key(key):
                out += "lost " + key + " "+make_red("|")
            elif not last.has_key(key) and curr.has_key(key):
                out += "add " + key + " "+make_red("|")
            elif last.has_key(key) and curr.has_key(key):
                for m in range(len(base[key])):
                    if last[key][m] != curr[key][m]:
                        #out += key + ":" + last[key][m] + "=>"+curr[key][m] + " "+make_red("|")
                        #0.94.5
                        #osd start
                        #  osd91:heartbeat_back_addr->10.20.29.186:1310/7475800=>heartbeat_back_addr->10.20.29.186:1338/8475800 |
                        #  osd91:up_from->32956=>up_from->32985 |
                        #  osd91:heartbeat_front_addr->10.20.29.186:1317/7475800=>heartbeat_front_addr->10.20.29.186:1339/8475800 |
                        #  osd91:up->0=>up->1 |osd91:last_clean_end->32955=>last_clean_end->32983 |
                        #  osd91:cluster_addr->10.20.29.186:1309/7475800=>cluster_addr->10.20.29.186:1337/8475800
                        #osd down
                        #  osd91:down_at->32954=>down_at->32981 |osd91:up->1=>up->0
                        #osd out (don't means osd91:up->1=>up->0, maybe osd is up)
                        #  osd91:down_at->33834=>down_at->33859 |osd91:up->1=>up->0
                        #  osd91:weight->1.0=>weight->0.0 |osd91:in->1=>in->0
                        #  sp case:
                        #    14:09:14.825890 33873:  osd91:weight->1.0=>weight->0.0 |osd91:in->1=>in->0
                        #    14:10:35.172827 33899:  osd91:down_at->33866=>down_at->33899 |osd91:up->1=>up->0
                        #  
                        #osd in
                        #  osd91:weight->0.0=>weight->1.0 |osd91:in->0=>in->1
                        #10.2.2
                        #osd91:up=>down, osd91:down=>up
                        o = key + ":" + last[key][m] + "=>"+curr[key][m] + " "+make_red("|")
                        if o.find("up->") != -1 or o.find("up=>down") != -1 or o.find("down=>up") != -1:
                            out += make_red(o)
                        else:
                            if options.show_detial:
                                out += o
    if last["pg_temp"] != curr["pg_temp"]:
        out += "pg_temp:" + str(last["pg_temp"]) + "=>"+str(curr["pg_temp"])+make_red("|")
    if out == "":
        out == "pool have a change??"
    print out_t, out
        
# for 0.9.45
def _get_history_0945(version):
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "get osdmap" + " -- --out om_tmp --version " + str(version)
    debug_print(cmd)
    out = commands.getoutput(cmd)
    cmd = ceph_dencoder + " import om_tmp type OSDMap decode dump_json"
    debug_print(cmd)
    out = commands.getoutput(cmd)
    json_out = json.loads(out)
    #print type(out), out
    #print type(json_out), json_out
    info = {}
    info["epoch"] = json_out["epoch"]
    info["pool"] = 0
    info["time_day"] = json_out["modified"].split()[0]
    info["time_hour"] = json_out["modified"].split()[1]
    info["max_osd"] = json_out["max_osd"]
    for data in json_out["pools"]:
        poolinfo = []
        poolname = "pool"+str(data["pool"])
        for k,v in data.items():
            if k == "pool":
                continue
            poolinfo.append(poolname+":"+k+"-"+str(v))
        info[poolname] = poolinfo
        info["pool"] += 1
    for data in json_out["osds"]:
        osdinfo = []
        osdname = "osd"+str(data["osd"])
        for k,v in data.items():
            if k == "osd":
                continue
            if k == "state":
                continue
            #if k == "up" or k == "in":
            #    osdinfo.append(make_red(k+"->"+str(v)))
            #else:
            osdinfo.append(k+"->"+str(v))
        info[osdname] = osdinfo
    info["pg_temp"] = len(json_out["pg_temp"])
    return info
# for 10.2.2
def _get_history(version):
    cmd = ceph_monstore_tool + " " + mondb_path + " " + "get osdmap" + " -- --readable=1 --version " + str(version)
    debug_print(cmd)
    out = commands.getoutput(cmd)
    info = {}
    for data in out.split("\n"):
        if data.startswith("epoch"):
            info["epoch"] = data.split()[1]
            info["pool"] = 0
            info["pg_temp"] = 0
        if data.startswith("modified"):
            info["time_day"] = data.split()[1]
            info["time_hour"] = data.split()[2]
        if data.startswith("pool"):
            info["pool"] += 1
        if data.startswith("max_osd"):
            info["max_osd"] = data.split()[1]
        if data.startswith("osd"):
            osdinfo = []
            osdinfo.append(data.split()[1])     # up or down
            osdinfo.append(data.split()[2])     # in or out
            osdinfo.append("uf" + data.split()[6])     # up_from
            osdinfo.append("ut" + data.split()[8])     # up_thru peering ok
            osdinfo.append("da" + data.split()[10])    # down_at
            osdinfo.append("lci" + data.split()[12])    # last_clean_interval
            osdinfo.append("" + data.split()[13])    # last_clean_interval
            osdinfo.append("" + data.split()[14])    # last_clean_interval
            osdinfo.append("" + data.split()[15])    # last_clean_interval
            osdinfo.append("" + data.split()[16])    # last_clean_interval
            osdinfo.append("" + data.split()[17])    # last_clean_interval
            #osdinfo.append("" + data.split()[18])    # last_clean_interval, there isn't id in some case, if only create it
                                                      # osd.41 down out weight 0 up_from 0 up_thru 0 down_at 0 last_clean_interval [0,0) :/0 :/0 :/0 :/0 exists,new
            info[data.split()[0]] = osdinfo
        if data.startswith("pool"):
            info[data.split(" ", 2)[0] + data.split(" ", 2)[1]] = data.split(" ", 2)[2]
        if data.startswith("pg_temp"):
            info["pg_temp"] += 1
    return info
            
def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    parser.add_option('-k', '--listkays', action="store_true", dest='listkeys', default=False, help='list all the keys')
    parser.add_option('-s', '--showversions', action="store_true", dest='showversions', default=False, help='show the version of all the map type')
    parser.add_option('-n', '--newtools', action="store_true", dest='newtools', default=True, help='use for ceph 10.2, default ')

    # print osdmap chenge list
    parser.add_option('-o', '--osdhistory', action="store_true", dest='history', default=False, help='show the history of osd map')
    parser.add_option('', '--sv', action="store", dest='start_version', default="", help='start verson, for osd history')
    parser.add_option('', '--ev', action="store", dest='end_version', default="", help='end verson, for osd history')
    parser.add_option('', '--sd', action="store_true", dest='show_detial', default=False, help='show the detail ,not only osd up and down, for osd history')
    '''common param'''
    parser.add_option('', '--ldtp', action="store", dest='ldbtool_path', default="/root/yu/usr/bin/", help='the dir which have dbtools(default /root/yu/usr/bin/)')
    parser.add_option('', '--dcp', action="store", dest='decode_path', default="/usr/bin/ceph-dencoder", help='the path of ceph-dencoder(default /usr/bin/ceph-dencoder)')
    parser.add_option('', '--dbp', action="store", dest='mondb_path', default="/var/lib/ceph/mon/mon.a/", help='the path which include store.db(default /var/lib/ceph/mon/mon.a/)')
    parser.add_option('-d', '--debugmode', action="store_true", dest='debug_mode', default=False, help='debug mode(default false)')
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

def check_param():
    global options
    global ceph_monstore_tool
    global ceph_kvstore_tool
    global ceph_dencoder
    global mondb_path
    
    if options.newtools and not os.path.exists(options.ldbtool_path + "ceph-monstore-tool"):
        print "%sceph-monstore-tool does not exist", options.ldbtool_path
        return False
    ceph_monstore_tool = options.ldbtool_path + "ceph-monstore-tool"
    if not options.newtools and not os.path.exists(options.ldbtool_path + "ceph-kvstore-tool"):
        print "%sceph-kvstore-tool does not exist", options.ldbtool_path
        return False
    ceph_kvstore_tool = options.ldbtool_path + "ceph-kvstore-tool"
    if not os.path.exists(options.decode_path):
        print "%s does not exist", options.decode_path
        return False
    #ceph_dencoder = options.ldbtool_path + "ceph-kvstore-tool"
    if not os.path.exists(options.mondb_path):
        print "%s does not exist", options.mondb_path
        return False
    mondb_path = options.mondb_path
    return True
    
def main(args=None):
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    global options
    global argvs
    global g_debug
    (options, argvs) = get_options(args)
    print argvs
    print options
    if options.debug_mode:
        g_debug = options.debug_mode
    if not check_param():
        print "cann't find tools or db, please check the param!!!"
        return
    if options.newtools:
        ceph_func["kvtool_cmd"] = " leveldb "
        ceph_func["show_version"] = _show_version
        ceph_func["get_history"] = _get_history
    else:
        ceph_func["kvtool_cmd"] = " "
        ceph_func["show_version"] = _show_version_0945
        ceph_func["get_history"] = _get_history_0945
    if options.version:
        print version
        return
    if options.listkeys:
        list_keys()        
    if options.showversions:
        show_versions()
    if options.history:
        if options.start_version == "" or options.end_version == "":
            print "need start and end version"
            return
        show_history(int(options.start_version), int(options.end_version))
    print "process"
if __name__ == "__main__":
    main()
