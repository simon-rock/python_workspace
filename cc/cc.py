#!/usr/bin/python
#encoding=utf-8
import os
import time
import urllib
############ read file 10M default  ###############
def read_in_chunks(file_path, chunk_size=1024*1024*10):
    #log.info("start read file: " + file_path)
    file_object = open(file_path)
    while True:
        chunk_data = file_object.read(chunk_size)
        if not chunk_data:
            break
        chunk_data += file_object.readline()
        yield chunk_data
def read_files( source_file ):       #check dir whether is empty
    files = []
    if not os.path.exists( source_file ):
        #log.info("source_file directory is not exists")
        return files
    contents = os.listdir( source_file ) #get files and directory in list
    for i in contents :
        i = os.path.join( source_file, i )
        if os.path.isfile( i ) :    #remove directory
            files.append( i )
            #log.info("add a file into list : " + i )
    return files                #return the answer(files or empty)
#dest_dir 分割后文件位置
#source_dir 源文件位置
#file 文件后缀序列 全局递增
def write_chunks(dest_dir, source_file, file_num = 100):
    n = file_num
    file_time = time.strftime( '%Y%m%d',time.localtime( time.time() ) ) 
    dest_file = dest_dir + file_time + str(n)
    fp = open(dest_file,'w')
    num = 1
    for chunk in read_in_chunks(source_file):
        if num == 3:
            fp.write(chunk)
            fp.close()
            #log.info("generate a new file : " + dest_file )
            n = n + 1
            num = 0
            dest_file = dest_dir + file_time + str(n)
            #log.info("start a new file : " + dest_file )
            fp = open(dest_file,'w')
        else:
            fp.write(chunk)
            num = num + 1
    if fp:
        fp.close()
    return n
def split_into_small_file(source_dir, dest_dir):
    file_names = read_files(source_dir)
    if not file_names :
        #log.info("directory is empty")
        return
    n = 100
    for source_file in file_names:
        print "process ",source_file
        n = write_chunks(dest_dir, source_file, n)
        #del_source_file = commands.getoutput("rm -rf " + source_file)
        #need_delete_files_nums = commands.getoutput("ls -l /data/proclog/log/storage/evicted/need_delete/disk/  | grep \"^-\" | wc -l")
        #if int(need_delete_files_nums) > 400:   # file size 9G
        #    break
        n = n + 1

# for testging yield
def fab(max): 
    n, a, b = 0, 0, 1 
    while n < max: 
        yield b 
        # print b 
        a, b = b, a + b 
        n = n + 1

if __name__=='__main__':
    source_dir=r"/home/yu/workspace/tfs_1.3.1/chinacache/data/disk/20150611"
    dest_dir=r"/home/yu/workspace/tfs_1.3.1/chinacache/need_delete/disk/"
    #split_into_small_file(source_dir, dest_dir)

    # for url
    line = r"p1.meituan.net%2F200.0%2Fshaitu%2F73270a0603dac5d3341c716c4bc4d6ae110336.jpg.webp@@@accept-encoding_gzip"
    print line
    myurl = urllib.unquote( line.strip() )
    print myurl
    myurl2 = urllib.unquote( line.strip() )
    print myurl2
    # then you can find the reason
    for n in fab(5):
        print n,
    f = fab(5)
    print f.next()
    print f.next()
    print f.next()
    # example
    #for line in open("test.txt"):   #use file iterators
    #    print line
