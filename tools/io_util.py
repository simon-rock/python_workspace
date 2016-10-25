#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
import re
import sys
import time
import csv
from string import strip
from optparse import OptionParser
import signal
####
sys_proc_path = '/proc/'
re_find_process_number = '^\d+$'
version = u"0.1"
g_debug = False
ISOTIMEFORMAT='%Y-%m-%d %X'

# out cvs
NO_GEN_FILE = "noout"
g_b_out = False
g_out_file = NO_GEN_FILE
####
# 通过/proc/$pid/io获取读写信息
####
def sigint_handler(signum, frame):
    return

def collect():
    _tmp = {}
    re_find_process_dir = re.compile(re_find_process_number)
    for i in os.listdir(sys_proc_path):
        if re_find_process_dir.search(i):
            try:
                _tmp[int(i)] = collect_one(i)
            except Exception,e:
                continue
                #print Exception,":",e
    return _tmp
def collect_one(i):
    global g_debug
    try:
        process_name = open("%s%s/stat" % (sys_proc_path, i), "rb").read().split(" ")[1]
        rw_io = open("%s%s/io" % (sys_proc_path, i), "rb").readlines()
    except Exception,e:
        if g_debug:
            print Exception,":",e
        raise
    for _info in rw_io:
        cut_info = strip(_info).split(':')
        if strip(cut_info[0]) == "read_bytes":
            read_io = int(strip(cut_info[1]))
        if strip(cut_info[0]) == "write_bytes":
            write_io = int(strip(cut_info[1]))
        if strip(cut_info[0]) == "syscr":
            read_cnt = int(strip(cut_info[1]))
        if strip(cut_info[0]) == "syscw":
            write_cnt = int(strip(cut_info[1]))
    return {"name":process_name, "read_bytes":read_io, "write_bytes":write_io, "syscr":read_cnt, "syscw":write_cnt}
def collect_info():
    _tmp = {}
    re_find_process_dir = re.compile(re_find_process_number)
    for i in os.listdir(sys_proc_path):
        if re_find_process_dir.search(i):
            try:                
                process_name = open("%s%s/stat" % (sys_proc_path, i), "rb").read().split(" ")[1]
                rw_io = open("%s%s/io" % (sys_proc_path, i), "rb").readlines()
                for _info in rw_io:
                    cut_info = strip(_info).split(':')
                    if strip(cut_info[0]) == "read_bytes":
                        read_io = int(strip(cut_info[1]))
                    if strip(cut_info[0]) == "write_bytes":
                        write_io = int(strip(cut_info[1]))
                    if strip(cut_info[0]) == "syscr":
                        read_cnt = int(strip(cut_info[1]))
                    if strip(cut_info[0]) == "syscw":
                        write_cnt = int(strip(cut_info[1]))
                _tmp[int(i)] = {"name":process_name, "read_bytes":read_io, "write_bytes":write_io, "syscr":read_cnt, "syscw":write_cnt}
            except Exception,e:
                print Exception,":",e
    return _tmp

def watch(_sleep_time, pids):
    global g_debug
    csv_data = []
    # time.localtime() return tuple
    print "-----",time.strftime( ISOTIMEFORMAT, time.localtime() ),"-----"
    process_info_list_frist = {}
    process_info_list_second = {}
    for pid in pids.split():
        try:
            process_info_list_frist[pid]= collect_one(pid)
        except Exception,e:
            continue
    time.sleep(_sleep_time)
    for pid in pids.split():
        try:
            process_info_list_second[pid] = collect_one(pid)
        except Exception,e:
            continue
    if g_debug:
        print process_info_list_frist
        print process_info_list_second

    if len(process_info_list_second) <= 0:
        print "no process"
        return
    # print title
    title = "%-15s" % "name"
    for pid in process_info_list_second.keys():
        for key in process_info_list_second[pid].keys():
            if key == "name":
                continue
            title += "%-15s" % key
        break
    title += "%-15s" % "read bytes/c" + "%-15s" % "write bytes/c"
    print title
    # print content
    for pid in process_info_list_second.keys():
        out = "%-15s" % pid
        for key in process_info_list_second[pid].keys():
            if key == "name":
                continue
            out +=  "%-15d" % (int(process_info_list_second[pid][key]) - int(process_info_list_frist[pid][key]))
        '''print sp data'''
        total_bytes = (int(process_info_list_second[pid]["read_bytes"]) - int(process_info_list_frist[pid]["read_bytes"]))
        total_cnt = (int(process_info_list_second[pid]["syscr"]) - int(process_info_list_frist[pid]["syscr"]))
        if total_cnt > 0:
            out += "%-15s" % str(total_bytes/total_cnt)
        else:
            out += "%-15d" % 0
        total_bytes = (int(process_info_list_second[pid]["write_bytes"]) - int(process_info_list_frist[pid]["write_bytes"]))
        total_cnt = (int(process_info_list_second[pid]["syscw"]) - int(process_info_list_frist[pid]["syscw"]))
        if total_cnt > 0:
            out += "%-15s" % str(total_bytes/total_cnt)
        else:
            out += "%-15d" % 0
        print out
        if g_b_out:
            csv_data.append(tuple((time.strftime( ISOTIMEFORMAT, time.localtime() ) +" "+ out).split()))
            print csv_data
    if g_b_out:
        csvfile = file(g_out_file, 'ab')
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
        csvfile.close()
def list_top(_sleep_time, _list_num):
    print "----------"
    _sort_read_dict = {}
    _sort_write_dict = {}
    _sort_syscr_dict = {}
    _sort_syscw_dict = {}
    # 获取系统读写数据
    process_info_list_frist = collect()
    time.sleep(_sleep_time)
    process_info_list_second = collect()
    # 将读数据和写数据进行分组，写入两个字典中
    #print  process_info_list_frist
    #print "-----"
    #print process_info_list_second
    for loop in process_info_list_second.keys():# 有些补全！！！！！
        second_read_v = process_info_list_second[loop]["read_bytes"]
        second_write_v = process_info_list_second[loop]["write_bytes"]
        try:
            frist_read_v = process_info_list_frist[loop]["read_bytes"]
        except:
            frist_read_v = 0
        try:
            frist_write_v = process_info_list_frist[loop]["write_bytes"]
        except:
            frist_write_v = 0
        # 计算第二次获得数据域第一次获得数据的差
        _sort_read_dict[loop] = second_read_v - frist_read_v
        _sort_write_dict[loop] = second_write_v - frist_write_v
        #print "-r-", loop,  process_info_list_second[loop]["syscr"], process_info_list_frist[loop]["syscr"]
        #print "-w-", loop,  process_info_list_second[loop]["syscw"], process_info_list_frist[loop]["syscw"]
        if process_info_list_frist.has_key(loop):
            _sort_syscr_dict[loop] = process_info_list_second[loop]["syscr"] - process_info_list_frist[loop]["syscr"]
        else:
            _sort_syscr_dict[loop] = process_info_list_second[loop]["syscr"] - 0
        if process_info_list_frist.has_key(loop):
            _sort_syscw_dict[loop] = process_info_list_second[loop]["syscw"] - process_info_list_frist[loop]["syscw"]
        else:
            _sort_syscw_dict[loop] = process_info_list_second[loop]["syscw"] - 0
    # 将读写数据进行排序
    sort_read_dict = sorted(_sort_read_dict.items(),key=lambda _sort_read_dict:_sort_read_dict[1],reverse=True)
    sort_write_dict = sorted(_sort_write_dict.items(),key=lambda _sort_write_dict:_sort_write_dict[1],reverse=True)
    sort_syscr_dict = sorted(_sort_syscr_dict.items(),key=lambda _sort_syscr_dict:_sort_syscr_dict[1],reverse=True)
    sort_syscw_dict = sorted(_sort_syscw_dict.items(),key=lambda _sort_syscw_dict:_sort_syscw_dict[1],reverse=True)
    #print sort_read_dict
    #print sort_write_dict
    #print sort_syscr_dict
    #print sort_syscw_dict
    # 打印统计结果
    #print _sort_syscr_dict
    #print _sort_syscw_dict
    print "pid            process               read(bytes)"
    for _num in range(min(_list_num, len(sort_read_dict))):
        read_pid = sort_read_dict[_num][0]
        res =  "%-15s" % read_pid
        res += "%-25s" % process_info_list_second[read_pid]["name"]
        res += "%-15s" % sort_read_dict[_num][1]
        print res
    print "pid            process               write(bytes)"
    for _num in range(min(_list_num, len(sort_write_dict))):
        write_pid = sort_write_dict[_num][0]
        res = "%-15s" % write_pid
        res += "%-25s" % process_info_list_second[write_pid]["name"]
        res += "%-15s" % sort_write_dict[_num][1]
        print res
    print "pid            process               read(count)"
    for _num in range(min(_list_num, len(sort_syscr_dict))):
        syscr_pid = sort_syscr_dict[_num][0]
        res = "%-15s" % syscr_pid
        res += "%-25s" % process_info_list_second[syscr_pid]["name"]
        res += "%-15s" % sort_syscr_dict[_num][1]
        print res
    print "pid            process               write(count)"
    for _num in range(min(_list_num, len(sort_syscw_dict))):
        syscw_pid = sort_syscw_dict[_num][0]
        res = "%-15s" % syscw_pid
        res += "%-25s" % process_info_list_second[syscw_pid]["name"]
        res += "%-15s" % sort_syscw_dict[_num][1]
        print res
    print "\n" * 1

def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    #list mode
    parser.add_option('-l', '--listmode', action="store_true", dest='list_mode', default=False, help='list top process with high io(default 3)')
    parser.add_option('-n', '', action="store", dest='top_num', default=3, help='list top(default 3)')
    #watch mode
    parser.add_option('-w', '--watchmode', action="store_true", dest='watch_mode', default=False, help='watch one process')
    parser.add_option('-p', '', action="store", dest='pids', default="1", help='watch pid(default 1)')
    
    parser.add_option('-s', '--skiptime', action="store", type="float", dest='skip_time', default=1, help='skip time(default 1s)')
    parser.add_option('-c', '--showcount', action="store", type="int", dest='show_count', default=10, help='showcount(default 10, if <0 , forver)')
    parser.add_option('-o', '--outfile', action="store", dest='out_file', default=NO_GEN_FILE, help='out csv mode(default no, means don not gen out file)')
    parser.add_option('-d', '--debugmode', action="store_true", dest='debug_mode', default=False, help='debug mode(default false)')

    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)
    return options, argvs

def main(args=None):
    #signal.signal(signal.SIGINT, sigint_handler)
    #signal.signal(signal.SIGHUP, sigint_handler)
    #signal.signal(signal.SIGTERM, sigint_handler)
    global options
    global argvs
    global g_debug

    global g_b_out
    global g_out_file
    
    (options, argvs) = get_options(args)
    print argvs
    print options
    if options.version:
        print version
        return
    if options.debug_mode:
        g_debug = options.debug_mode
    if options.out_file != NO_GEN_FILE:
        g_b_out = True
        g_out_file = options.out_file
    for i in range(options.show_count if options.show_count > 0 else 86400):
        if options.list_mode:
            list_top(options.skip_time, options.top_num)
        if options.watch_mode:
            watch(options.skip_time, options.pids)
if __name__ == "__main__":
    main()
