#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
import re
import sys
import time
import csv
import commands
from string import strip
from optparse import OptionParser
import signal
####
sys_proc_path = '/proc/'
re_find_process_number = '^\d+$'
version = u"0.22"
g_debug = False
ISOTIMEFORMAT='%Y-%m-%d %X'
dev_io_match = u""
# out cvs
NO_GEN_FILE = "noout"
g_b_out = False
g_out_file = NO_GEN_FILE
####
# 通过/proc/$pid/io获取读写信息
####
def debug_print(str):
    if g_debug:
        print "debug: ", str
def sigint_handler(signum, frame):
    global options
    if options.analy_mode:
        cmd = "echo 0 > /proc/sys/vm/block_dump"
        out = commands.getoutput(cmd)
        print out
    sys.exit()
def pre_analy_mode():
    cmd = "echo 1 > /proc/sys/vm/block_dump"
    out = commands.getoutput(cmd)
    print out
def analy_devs(dev_names, show_lwp):
    ret = {}
    #test string
    #inode = "[4738409.496207] nginx(28798): dirtied inode 6554526 (?) on sde2"
    #inode2 = "nginx(28798): dirtied inode 6554526 (?) on sde2"
    #block = "[4762222.817648] ceph-osd(21875): READ block 5929149400 on sdj (8 sectors)"
    #block2 = "ceph-osd(3090221): READ block 3927644160 on sdf"
    #prog_block = re.compile("\[(\S+)\] (\S+)\((\d+)\): (\S+) block \d+ on (\S+) \((\d+)")
    #prog_inode = re.compile("\[(\S+)\] (\S+)\((\d+)\): (\S+) inode \d+ .* on (\S+)")
    #prog_block = re.compile("\[\S+\] (\S+)\((\d+)\): (\S+) block \d+ on (\S+) \((\d+)")    
    #prog_inode = re.compile("\[\S+\] (\S+)\((\d+)\): (\S+) inode \d+ .* on (\S+)")
    prog_block = re.compile("(\[\S+\] )?(\S+)\((\d+)\): (\S+) block \d+ on (\S+)\s?\(?(\d+)?")
    prog_inode = re.compile("(\[\S+\] )?(\S+)\((\d+)\): (\S+) inode \d+ .* on (\S+)")
    # define
    time_index = 1      #??
    pn_index = 2
    pid_index = 3
    io_type_index = 4
    dev_index = 5
    io_size_index = 6   #??
    
    cmd = "dmesg -c | grep -E \" "
    if len(dev_names) > 0:
        cmd += dev_names[0]
    for i in range(1, len(dev_names)):
        cmd += "| " + dev_names[i]
    cmd += "\""
    debug_print(cmd)
    out = commands.getoutput(cmd)

    '''LWP <=> PID'''
    lwp_pid_map = {}
    cmd = "ps -eLf | awk '{print $2\" \"$4}' | grep -v PID}"
    out2 = commands.getoutput(cmd)
    for line in out2.split("\n"):
        lwp_pid_map[line.split()[1]] = line.split()[0]
    if out == "":
        print "-----empty-----"
        return
    for line in out.split("\n"):
        debug_print(line)
    #for line in open("/mnt/hgfs/workspace/out", "rb").readlines():
        #print line, line.find("block"), line.find("inode")
        if line.find("block") != -1:
            res = re.match(prog_block, line)
            debug_print(res.groups())

        if line.find("inode") != -1:
            res = re.match(prog_inode, line)
            debug_print(res.groups())

        if ret.has_key(res.group(dev_index)):
            dev_item = ret[res.group(dev_index)]
            if dev_item.has_key(res.group(pid_index)):
                lwp_item = dev_item[res.group(pid_index)]
                lwp_item[res.group(io_type_index)] += 1
                if line.find(" block ") != -1:
                    if res.group(io_size_index) != None:
                        lwp_item[res.group(io_type_index)+"_size"] += int(res.group(io_size_index))
            else:
                lwp_item = {}
                lwp_item["name"] = res.group(pn_index)
                lwp_item["READ"] = 0
                lwp_item["WRITE"] = 0
                lwp_item["dirtied"] = 0
                lwp_item["READ_size"] = 0
                lwp_item["WRITE_size"] = 0
                lwp_item[res.group(io_type_index)] += 1
                if line.find(" block ") != -1:
                    if res.group(io_size_index) != None:
                        lwp_item[res.group(io_type_index)+"_size"] += int(res.group(io_size_index))
                dev_item[res.group(pid_index)] = lwp_item
        else:
            new_lwp_item = {}
            new_lwp_item["name"] = res.group(pn_index)
            new_lwp_item["READ"] = 0
            new_lwp_item["WRITE"] = 0
            new_lwp_item["dirtied"] = 0
            new_lwp_item["READ_size"] = 0
            new_lwp_item["WRITE_size"] = 0
            new_lwp_item[res.group(io_type_index)] += 1
            if line.find(" block ") != -1:
                if res.group(io_size_index) != None:
                    new_lwp_item[res.group(io_type_index)+"_size"] += int(res.group(io_size_index))
            dev_item = {}
            dev_item[res.group(pid_index)] = new_lwp_item
            ret[res.group(dev_index)] = dev_item
    '''print ret'''
    print "-----",time.strftime( ISOTIMEFORMAT, time.localtime() ),"-----", "%15s %15s %15s %15s %15s" % ("READ", "WRITE", "dirtied", "READ_size(KB)", "WRITE_size(KB)")
    for dev in ret.keys():
        print dev
        dev_item = ret[dev]
        if show_lwp:
            for lwp in dev_item.keys():
                lwp_item = dev_item[lwp]
                print "%15s %15s %15d %15d %15d %15d %15d" % (lwp, lwp_item["name"], lwp_item["READ"], lwp_item["WRITE"], lwp_item["dirtied"], lwp_item["READ_size"]/2, lwp_item["WRITE_size"]/2 )
        else:
            pids = {}
            for lwp in dev_item.keys():
                lwp_item = dev_item[lwp]
                if lwp_pid_map.has_key(lwp):
                    pid = lwp_pid_map[lwp]
                    if pids.has_key(pid):
                        pids[pid]["READ"] += lwp_item["READ"]
                        pids[pid]["WRITE"] += lwp_item["WRITE"]
                        pids[pid]["dirtied"] += lwp_item["dirtied"]
                        pids[pid]["READ_size"] += lwp_item["READ_size"]
                        pids[pid]["WRITE_size"] += lwp_item["WRITE_size"]
                    else:
                        pids[pid] = lwp_item
                else:
                    pids[lwp + "_die"] = lwp_item
            for pid in pids.keys():
                pid_item = pids[pid]
                print "%15s %15s %15d %15d %15d %15d %15d" % (pid, pid_item["name"], pid_item["READ"], pid_item["WRITE"], pid_item["dirtied"], pid_item["READ_size"]/2, pid_item["WRITE_size"]/2 )
                
'''called by watch mode'''
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

'''analy /proc/pid/stat'''
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

'''called by list mode'''
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

'''watch mode'''
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
    title = "%-15s" % "pid(name)"
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
        out = "%-15s" % (pid + process_info_list_second[pid]["name"])
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
'''list top num process with high IO'''
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

'''analy mode'''
def analy_mode(_sleep_time, dev_names, show_lwp):
    global g_debug
    # pre
    pre_analy_mode()
    while True:
        analy_devs(dev_names, show_lwp)
        time.sleep(_sleep_time)

def get_pids(sp_str):
    pids = ""
    cmd = "ps aux | grep " + sp_str + " | grep -v grep | grep -v io_util | awk '{print $2}'"
    out = commands.getoutput(cmd)
    for data in out.split():
        pids += data + " "
    return pids
def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    parser.add_option('-v', '--version', action="store_true", dest='version', default=False, help='print version')
    #analy dev mode
    parser.add_option('-a', '--analymode', action="store_true", dest='analy_mode', default=False, help='analy the sp. dev(e.g. -a sda)')
    parser.add_option('', '--show_lwp', action="store_true", dest='show_lwp', default=False, help='show the lwp (default False) ')
    #list mode
    parser.add_option('-l', '--listmode', action="store_true", dest='list_mode', default=False, help='list top process with high io(default 3)')
    parser.add_option('-n', '', action="store", dest='top_num', default=3, help='list top(default 3)')
    #watch mode
    parser.add_option('-w', '--watchmode', action="store_true", dest='watch_mode', default=False, help='watch one process')
    parser.add_option('-p', '', action="store", dest='pids', default="1", help='watch pids(default 1, you can watch some pids "1 2 3")')
    parser.add_option('--cmd', '', action="store", dest='cmd', default="", help='watch pids which name have these string (default "", will ignore -p )')
    
    parser.add_option('-s', '--skiptime', action="store", type="float", dest='skip_time', default=1, help='skip time(default 1s)')
    parser.add_option('-c', '--showcount', action="store", type="int", dest='show_count', default=10, help='showcount(default 10, if <0 , forver)')
    parser.add_option('-o', '--outfile', action="store", dest='out_file', default=NO_GEN_FILE, help='out csv mode(default no, means don not gen out file)')
    parser.add_option('-d', '--debugmode', action="store_true", dest='debug_mode', default=False, help='debug mode(default false)')

    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)
    return options, argvs

def main(args=None):
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
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
0        g_debug = options.debug_mode
    if options.out_file != NO_GEN_FILE:
        g_b_out = True
        g_out_file = options.out_file
    if options.analy_mode:
        analy_mode(options.skip_time, argvs, options.show_lwp)
    for i in range(options.show_count if options.show_count > 0 else 86400):
        if options.list_mode:
            list_top(options.skip_time, options.top_num)
        if options.watch_mode:
            if options.cmd == "":
                watch(options.skip_time, options.pids)
            else:
                pids = get_pids(options.cmd)
                watch(options.skip_time, pids)
if __name__ == "__main__":
    main()
