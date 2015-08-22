#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import os
import shutil
import os
import glob
import sys
from stat import *
import string # for cmp, replace,s.strip() .lstrip() .rstrip(',')

from optparse import OptionParser, SUPPRESS_HELP
pwblock_set_all_ds = set()
block_set_ds = set()
wblock_set = set()
def get_options(args=None):
    """Parse command line options and parameters."""
    parser = OptionParser(add_help_option=False, usage='%prog <arg> [option]', description="")

    parser.add_option('', '--wb', action='store', default="log_4", dest='logwb', help='wblock, from showssm -t 4')
    parser.add_option('', '--ids', action='store', default="log_16", dest='logids', help="info of ds, from showssm -t 16")
    parser.add_option('-l', '--listds', action='store_true', default=False, dest='blistds', help="only list server info")
    parser.add_option('-d', '--detail', dest='bdetail', action='store_true', default=False)
    parser.add_option('-h', '--help', dest='help', action='store_true', default=False)

    global HELP
    HELP = parser.format_help().strip()
    options, args = parser.parse_args(args)
    return options, args

def analy_info_of_wb(file):
    fp = open(file, "r")
    line = fp.read().split()
    wblock_cnt = line[1].replace("(","").replace(")","")
    for item in range(3, len(line)):
        if cmp(line[item], "SUCCESS") == 0:
            break
        wblock_set.add(line[item])
    if string.atoi(wblock_cnt) != len(wblock_set):
        print "analy logwb failed"
    else:
        print "wb cnt : ",len(wblock_set)

def analy_info_of_ds(file, ds_info, blistds):
    fp = open(file, "r")
    server_cnt = 0
    for line in fp.readlines():
        server_block = line.split()
        if server_block[0].find(':') == -1:
            continue
        block_cnt = 0
        server_cnt += 1
        wblock_cnt = 0
        pwblock_cnt = 0
        cur_cnt = 0
        bpwblock = False
        ds_i = {}
        block_set_ds = set()
        pwblock_set_ds = set()
        for item in range(2, len(server_block)):
            if server_block[item].endswith( ")"):
                pwblock_cnt = cur_cnt
                continue
            if server_block[item].startswith("("):
                wblock_cnt = cur_cnt
                cur_cnt = 0
                bpwblock = True
            cur_cnt += 1
            server_block[item] = server_block[item].replace("(", "")
            if bpwblock:
                pwblock_set_ds.add(server_block[item])
            else:
                block_set_ds.add(server_block[item])
        if len(pwblock_set_all_ds) != 0:#
            err = pwblock_set_all_ds & pwblock_set_ds
            if len(err) != 0:
                print "error"
        pwblock_set_all_ds.update(pwblock_set_ds)
        ds_i["w"] = block_set_ds
        ds_i["pw"] = pwblock_set_ds
        if blistds:
            #print server_cnt, server_block[0], wblock_cnt, pwblock_cnt
            print server_cnt, server_block[0], len(ds_i["w"]), len(ds_i["pw"])
        ds_info[server_block[0]] = ds_i
        
    print "block cnt from ds : ", len(pwblock_set_all_ds)
    fp.close()

def find_block(block_id, ds_info):
    #print ds_info
    bfind = False
    for (k, v) in ds_info.items():
        if block_id in v["pw"]:
            print block_id, "=>", k, "[pw]"
            bfind = True
            break
        elif block_id in v["w"]:
            print block_id, "=>", k, "[w]"
            bfind = True
            break
    if not bfind:
        print block_id, "=>", "no find"
def main(argv=None):
    (options, argv) = get_options(argv)
    if options.help:
        print HELP
        return
    ds_info = {}
    analy_info_of_ds(options.logids, ds_info, options.blistds)
    analy_info_of_wb(options.logwb)

    ds_b = pwblock_set_all_ds - wblock_set
    b_ds = wblock_set - pwblock_set_all_ds
    
    
    print "server info - wblock : ",len(ds_b)
    if options.bdetail:
        for v in ds_b:
            find_block(v, ds_info)
    print "=========="
    print "wblock - server info : ",len(b_ds)
    if options.bdetail:
        for v in b_ds:
            find_block(v, ds_info)
if __name__ == "__main__":
    main()
