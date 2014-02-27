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

def process_file(in_file, out):
    fp = open(in_file, 'r')
    out_path = os.path.join(out, "o.svg")
    print out_path
    ofp = open(out_path, 'w')
    for line in fp.readlines():
        if cmp(line[0:6], "    <g") == 0: #s.strip() .lstrip() .rstrip(',') 去空格及特殊符号
            g = line
            g = g.replace(r"/>", r">")
            ofp.write(g)
        elif cmp(line[0:6], "    <p") == 0:
            path = line.replace("-width:1", "-width:50")
            path = path + "    </g>\n"
            ofp.write(path)
        else:
            ofp.write(line)
    fp.close()
    ofp.close()
if __name__ == "__main__":
    process_file(r"d:\python_workspace\src\file\1.svg", r".")

