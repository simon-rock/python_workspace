#!/usr/bin/env python
#coding: utf-8
#
# ceph daemon osd.17 config  set debug_optracker 5
# so, you can filter the sp. log using tailf osd.17.log | ananly_ceph_log.py -r [-f event or all] [-t print_event or all] [-c cost or 0]
#
# usage : | analy_ceph_log.py -r [-f EVENT -c COST] [-t PEVENT] [-d]
import re
import string
import os
import datetime
import time
import sys
import cPickle as p
from optparse import OptionParser
import signal

is_sigint_up = False
g_debug = False
TASKS = {}
TASKS_LINE = 2

EVENT_STAT = {}

redc = "\033[1;31;40m"
defaultc="\033[0m"
def make_red(s):
    return redc+s+defaultc

zerotime = datetime.datetime.strptime("2000-1-1 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")

def debug_print(str):
    global g_debug
    if g_debug:
        #print "debug: ", str
        print make_red("debug: "), str
def debug_str(str):
    global g_debug
    if g_debug:
        return str
    else:
        return ""
def sigint_handler(signum, frame):
    global is_sigint_up
    global EVENT_STAT
    is_sigint_up = True
    print "catch interrupt signal!"
    time.sleep(1)
    print ("%-55s "%("key")), ("%-13s "%("avg_cost")),("%-13s "%("max")),("%-13s "%("min")),("%-13s "%("total_count"))
    for key, val in EVENT_STAT.items():
        print ("%-55s "%(key)), val["avg_cost"], val["max"], val["min"],  val["total_count"]

test_str_0945 = r'2015-12-14 03:15:20.672735 7ff19db41700  5  common/TrackedOp.cc:287 -- op tracker -- seq: 96452, time: 2015-12-14 03:15:20.672371, event: header_read, op: osd_sub_op(client.6125.0:270 4.4 65639084/gc.29/head//4 [] v 94\'14753 snapset=0=[]:[] snapc=0=[])'
test_str_1025 = r'2017-05-11 11:18:08.216603 7fa5063e8700  5  common/TrackedOp.cc:292 -- op tracker -- seq: 4176973, time: 2017-05-11 11:18:08.216603, event: waiting for subops from 5,22, op: osd_op(client.1212883.0:680 28.9de6e907 obj_delete_at_hint.0000000086 [call lock.lock] snapc 0=[] ondisk+write+known_if_redirected e22596)'
def process(log_path, out):
    global TASKS
    fp = open(log_path, 'r')
    out_path = os.path.join(out, "out")
    #print out_path
    for line in fp.readlines():
        get_seq_info(line)
    fp.close()
    #dump to out file
    f = file(out_path, "w")
    p.dump(TASKS, f)
    f.close
def load_analyzed_file(analyzed):
    global TASKS
    f = file(analyzed)
    TASKS = p.load(f)
'''
TASKS struct
seq -> linef
    -> linef2
    -> line
    -> line2
    -> event_name time cost info
    -> event_name time cost info
    ...
seq -> ...
'''
def get_seq_info(line, real = False):
    debug_print(line)
    if is_sigint_up:
        return
    #prog = re.compile(".* -- op tracker -- seq: (\d+), time: (\S+ \S+),.* event: (\S+),")
    prog = re.compile(".* -- op tracker -- seq: (\d+), time: (\S+ \S+),.* event: (.+), op: (.+)") # update for ceph 10.2.5
    res = re.match(prog, line)
    if res is None:
        debug_print("res is None")
        return
    debug_print(res.groups())
    if len(res.groups()) < 3:
        return
    co_time = datetime.datetime.strptime(res.group(2), "%Y-%m-%d %H:%M:%S.%f")
    seq =  res.group(1)
    event_name = res.group(3)
    other_info = res.group(4)
    # check if exist (seq) (seq:44459)
    ss = re.compile("\(seq:\d+\)")
    event_name = ss.sub("", event_name)
    if not TASKS.has_key(seq):
        tmp = []
        #tmp.append(("main_s", zerotime, datetime.timedelta(microseconds = 0), ""))
        #tmp.append(("replica_s", zerotime, datetime.timedelta(microseconds = 0), ""))
        tmp.append(("main_cur", co_time, datetime.timedelta(microseconds = 0), ""))
        tmp.append(("replica_start", zerotime, datetime.timedelta(microseconds = 0), ""))
        tmp.append((event_name, co_time, datetime.timedelta(microseconds = 0), other_info))
        TASKS[seq] = tmp
    else:
        item = TASKS[seq]
        #print item, len(item), item[len(item) - 1][1]
        #cost = co_time - item[len(item) - 1][1]
        cost = cal_cost(item, event_name, co_time)
        item.append((event_name, co_time, cost, other_info))
        global options
        if real and ((event_name == "done" and (options.event != options.pevent or options.event == "all"))or ( event_name == options.event and options.event == options.pevent)):        
            global argvs
            if filt_date((seq, item), options.event, int(options.cost)):
                print_data((seq, item), options.pevent)
    if event_name == "done":
        proc_stat(TASKS[seq])
        del TASKS[seq]

    #print tasks
    #print "-------------"
    ''' 
    timeArray = time.strptime(res.group(1), "%Y-%m-%d %H:%M:%S.%f")
    print timeArray
    timeStamp = time.mktime(timeArray)
    print timeStamp

p
    time2 = "2015-12-14 03:15:20.672735"
    time3 = "2015-12-14 03:15:20.672835"
    #print type(datetime.datetime.strptime(time2, "%Y-%m-%d %H:%M:%S.%f"))
    datetime_t2 = datetime.datetime.strptime(time2, "%Y-%m-%d %H:%M:%S.%f")
    datetime_t3 = datetime.datetime.strptime(time3, "%Y-%m-%d %H:%M:%S.%f")
    print datetime_t3 - datetime_t2
    '''
'''
cal the cost for every stop
'''
def cal_cost(item, event_name, co_time):
    ''' is replica '''
    if event_name.find("waiting for subops from ") != -1:
        item[1]= ("replica_start", co_time, datetime.timedelta(microseconds = 0), "")

    ''''''
    if event_name.find("sub_op_commit_rec") != -1 or event_name.find("sub_op_applied_rec") != -1:
        ret_cost= co_time - item[1][1]
    else:
        ret_cost= co_time - item[0][1]
        print co_time, " --- ", item[0][1] , "--", ret_cost
        item[0]= ("main_cur", co_time, datetime.timedelta(microseconds = 0), "")
    return ret_cost

'''
proc_stat
cal the max, min, avgcost for the part of request
'''
def proc_stat(req):
    global EVENT_STAT
    if not check_req(req):
        return
    '''the first request may not been caught'''
    if len(req) < TASKS_LINE + 1 or req[TASKS_LINE][0] != "queued_for_pg" :
        return
    for val in req:
        if not EVENT_STAT.has_key(val[0]):
            item = {}
            item["max"] = val[2]
            item["min"] = val[2]
            item["avg_cost"] = val[2]
            item["total_count"] = 1
            EVENT_STAT[val[0]] = item
        else:
            try:
                item = EVENT_STAT[val[0]]
                if item["max"] < val[2]:
                    item["max"] = val[2]
                if item["min"] > val[2]:
                    item["min"] = val[2]
                item["avg_cost"] = ((item["avg_cost"]*item["total_count"]) + val[2])/(item["total_count"]+1)
                item["total_count"] += 1
            except Exception,ex:
                print Exception,":",ex,"--",val[2]
    if not EVENT_STAT.has_key("reqcost"):
        item = {}
        ret = get_all_time(req)
        item["max"] = ret
        item["min"] = ret
        item["avg_cost"] = ret
        item["total_count"] = 1
        EVENT_STAT["reqcost"] = item
    else:
        try:
            ret = get_all_time(req)
            item = EVENT_STAT["reqcost"]
            if item["max"] < ret:
                item["max"] = ret
            if item["min"] > ret:
                item["min"] = ret
            item["avg_cost"] = ((item["avg_cost"]*item["total_count"]) + ret)/(item["total_count"]+1)
            item["total_count"] += 1
        except Exception,ex:
            print Exception,":",ex,"--",val[2]
'''check if the req is main req'''                
def check_req(req):
    global options
    if options.onlymain:
        for val in req:
            if val[0].find("waiting for subops from") != -1:
                return True
        return False
    else:
        return True
def statistics(filter, event, v):
    # analy tasks
    global TASKS
    total_num = len(TASKS)
    success_num = 0
    event_stat = {}
    all_done_time = datetime.datetime.now() - datetime.datetime.now()
    
    for key, vals in TASKS.items():
        #add filter
        if not filter(vals, event, v):
            continue
        for val in vals:
            if not event_stat.has_key(val[0]):
                item = {}
                item["max"] = val[2]
                item["min"] = val[2]
                item["total_cost"] = val[2]
                item["total_count"] = 1
                event_stat[val[0]] = item
            else:
                try:
                    item = event_stat[val[0]]
                    if item["max"] < val[2]:
                        item["max"] = val[2]
                    if item["min"] > val[2]:
                        item["min"] = val[2]
                    item["total_cost"] += val[2]
                    item["total_count"] += 1
                except Exception,ex:
                    print Exception,":",ex,"--",val[2]
            if val[0] == "done":
                success_num += 1
                all_done_time += get_all_time(vals)
    for key, val in event_stat.items():
        print ("%-55s "%(key)), val["total_cost"]/val["total_count"], val["max"], val["min"], val["total_cost"], val["total_count"]
    if success_num > 0:
        print success_num ,"/", total_num, " -avg- ", all_done_time/success_num

def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    #parser.add_option('-d', '--outputdir',action='store', dest='outdir', default='.', help='*.BIN files output directory')
    #parser.add_option('-t', '--TT', action="store_true", dest='tt_nt', default=False, help='process TT landmark, default NT')
    #parser.add_option('-p', '--processconfig', action="store_true", dest='processconfig', default=False, help='only process landmark_table')
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    parser.add_option('-a', '--analyzedfile', action="store_true", dest='analyzed', default=False, help='open a analyzed file')
    parser.add_option('-o', '--outnanlyzed',action='store', dest='outdir', default='.', help='dir of analyzed file')
    parser.add_option('-c', '--threshold',action='store', dest='cost', default='0', help='microseconds(us), only analy the event which cost over the threshold')
    parser.add_option('-p', '--print', action="store_true", dest='print_only', default=False, help='print only through the filter')
    # for real time
    parser.add_option('-r', '--realtime', action="store_true", dest='realtime', default=False, help='realtime analy')
    parser.add_option('-m', '--onlymain', action="store_true", dest='onlymain', default=False, help='only analy main req')
    parser.add_option('-f', '--filter_event', action="store", dest='event', default="all", help='event name')
    parser.add_option('-t', '--print_event', action="store", dest='pevent', default="all", help='event name')
    parser.add_option('-d', '--debugmode', action="store_true", dest='debug_mode', default=False, help='debug mode(default false)')    
    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)
    
    if not options.realtime and  len(argvs) < 1 and not options.version:
        parser.error("Please specify the directory of the file to be processed.")
    return options, argvs

def print_sp_data(filter, event_name, event_cost, pevent):
    global TASKS
    '''for key, vals in TASKS.items():
        for val in vals:
            if val[0] == event_name and val[2] == datetime.timedelta(microseconds = event_cost):
                print key,"-->"
                for val in vals:
                    print val'''
    for item in TASKS.items():
        if filter(item, event_name, event_cost):
            print_data(item, pevent)

def data_filter(item, event_name, event_cost):
    if len(item) > TASKS_LINE and get_all_time(item) > datetime.timedelta(microseconds = event_cost):
        return True
    else:
        return False
'''seq_time is (seq, task_item)'''
def filt_date(seq_item, event_name, event_cost):
    if event_name == "all":
         if len(seq_item[1]) > TASKS_LINE and get_all_time(seq_item[1]) > datetime.timedelta(microseconds = event_cost):
             return True
    else:
        for val in seq_item[1]:
             if val[0] == event_name and val[2] > datetime.timedelta(microseconds = event_cost):
                 return True
    return False
def print_data(item, event_name):
    for val in item[1]:
        if event_name == "all" or val[0] == event_name :
            print item[0],"-->%-35s"% val[0], debug_str(val[1]), val[2], debug_str(val[3])
'''cal the total cost of request '''
def get_all_time(item):
    return (item[len(item)-1][1] - item[TASKS_LINE][1])

def realtime_analy():
    for line in sys.stdin:
         get_seq_info(line, True)
def main(args=None):
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    global options
    global argvs
    global g_debug
    (options, argvs) = get_options(args)
    #if len(sys.argv) == 0:
    #    print "input log path"
    #    return
    print argvs
    print options
    if options.debug_mode:
        g_debug = options.debug_mode
    if options.version:
        print "current version 0.4"
        return
    if options.realtime:
        realtime_analy()
        print ("%-55s "%("key")), ("%-13s "%("avg_cost")),("%-13s "%("max")),("%-13s "%("min")),("%-13s "%("total_count"))
        for key, val in EVENT_STAT.items():
            print ("%-55s "%(key)), val["avg_cost"], val["max"], val["min"],  val["total_count"]
        return
    if options.analyzed:
        print "load midfile"
        load_analyzed_file(argvs[0])
    else:
        print "start gen midfile"
        process(argvs[0], options.outdir)
    #process(sys.argv[1], "./")
    #process("testlog", "./")
    #pause = raw_input()
    print "-----"
    if options.print_only:
        print_sp_data(filt_date, options.event, int(options.cost), options.pevent)
    else:
        print "statistics"
        statistics(data_filter, options.event, int(options.cost))
if __name__ == "__main__":
    main()
