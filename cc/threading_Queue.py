#!/usr/bin/python
#encoding=utf-8
import os,sys
import time
import socket
import subprocess
import ConfigParser
import threading
import Queue
import urllib
import httplib
import json
import random
import logging
import commands

format='%(asctime)s - %(filename)s - [line:%(lineno)d] - %(levelname)s - %(message)s'
formatter = logging.Formatter(format)
log = logging.getLogger('root.test')
log.setLevel(logging.INFO)

def check_port( ip, port ):            #check ip&&port is alive
    sk = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    sk.settimeout( 3 ) 
    try:
        sk.connect( ( ip, port ) ) 
        sk.close()
        return True
    except Exception:
        sk.close()
        return False

def read_files( source_file ):       #check dir whether is empty
    files = []
    if not os.path.exists( source_file ):
        log.info("source_file directory is not exists")
        return files
    contents = os.listdir( source_file ) #get files and directory in list
    for i in contents :
        i = os.path.join( source_file, i )
        if os.path.isfile( i ) :    #remove directory
            files.append( i )
            log.info("add a file into list : " + i )
    return files                #return the answer(files or empty)

############ read file 10M default  ###############
def read_in_chunks(file_path, chunk_size=1024*1024*10):
    log.info("start read file: " + file_path)
    file_object = open(file_path)
    while True:
        chunk_data = file_object.read(chunk_size)
        if not chunk_data:
            break
        yield chunk_data

############ 10G file split into 30MB files use 3 min  #############
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
            log.info("generate a new file : " + dest_file )
            n = n + 1
            num = 0
            dest_file = dest_dir + file_time + str(n)
            log.info("start a new file : " + dest_file )
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
        log.info("directory is empty")
        return
    n = 100
    for source_file in file_names:
        n = write_chunks(dest_dir, source_file, n)
        del_source_file = commands.getoutput("rm -rf " + source_file)
        #need_delete_files_nums = commands.getoutput("ls -l /data/proclog/log/storage/evicted/need_delete/disk/  | grep \"^-\" | wc -l")
        #if int(need_delete_files_nums) > 400:   # file size 9G
        #   break
        n = n + 1

#-------------------------------------------------
stop=False
class WorkManager( object ):
    def __init__(self, need_delete_urls_dir, thread_num=10):
        self.work_queue = Queue.Queue()
        self.threads =[]
        self.__init_thread_pool(thread_num)
        global stop
        stop = False
        while True:
            files = read_files( need_delete_urls_dir )
            for file_dir in files:
                while ( self.work_queue.qsize() > 2000 ):
                    time.sleep( 2 )
                finput = open( file_dir, 'r' )
                #for line in finput.readlines():             #read a file
                #   myurl = urllib.unquote( line.strip() )
                #   self.add_job( do_job, myurl )
                num = 0
                col = []
                for line in finput.readlines():
                    myurl = urllib.unquote( line.strip() )
                    col.append(myurl)
                    num=num+1
                    if num == 500:
                        num = 0
                        self.add_job( do_job, col )
                        col = []
                fnull = open( os.devnull,'w')
                res = subprocess.call("rm -f " + file_dir, shell=True,stdout=fnull,stderr=fnull )
                fnull.close()
                if res:
                    log.info("delete file error at thread")
                    break
                finput.close()
                now_time = time.strftime( '%H:%M:%S',time.localtime( time.time() ) )    #check time wether at 00:00:00 and 07:00:00
                if cmp( now_time,"00:00:00") < 0 or cmp( now_time,"21:00:00") >= 0:
                    break

            stop = True
            print "main thread exit"
            break
    def __init_thread_pool( self, thread_num ):
        for i in range( thread_num ):
            self.threads.append( Work( self.work_queue) )

    def add_job( self, func, args ):
        self.work_queue.put( ( func, args ) )

    def wait_allcomplete( self ):
        for item in self.threads:
            if item.isAlive():
                item.join()

class Work( threading.Thread ):
    def __init__( self, work_queue ):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.start()

    def run(self):
        global stop
        while True:
            try:
                if stop == True and self.work_queue.empty():
                    print "stop = true"
                    break
                if self.work_queue.empty():
                    print "work_queue is empty"
                    time.sleep(1)
                    continue
                do,args = self.work_queue.get(block=False)
                do( args )
                self.work_queue.task_done()
            except Queue.Empty:
                time.sleep(1)
                print "Queue.Empty"
                continue
            except Exception,e:
                log.info("this is error in run" + str(e))
cnt = 0
cnt_num = 0
mylock = threading.RLock()
'''
def do_job( args ):
    try:
        global cnt
        global cnt_num

        mylock.acquire()
        cnt += 1
        cnt_num += 1
        if cnt >= 200000 :
            log.info("this is NO. " + str(cnt_num) )
            cnt -= 200000
        mylock.release()

        host = "127.0.0.1"
        #headers = {"Store-Control":"ssd","Content-type":"application/json"}
        conn = httplib.HTTPConnection( host, 770 )
        method = 'GET'
        uri = '/delete/' + ''.join(args)
        conn.request( method, uri )
        res = conn.getresponse()
        if res.status != 200:
            log.info(" status is not 200---->" + uri)
    except Exception,e:
        log.info("--------http error-----" + ''.join(args) )
        log.info("--------http error-----" + str(e))
    finally:
        if conn:
            conn.close()
'''
def do_job( args ):
    try:
        global cnt
        global cnt_num

        mylock.acquire()
        cnt += 1
        cnt_num += 1
        if cnt >= 200000 :
            log.info("this is NO. " + str(cnt_num) )
            cnt -= 200000
        mylock.release()

        host = "127.0.0.1"
        conn = httplib.HTTPConnection( host, 770 )
        method = 'POST'
        uri = '/mdelete/'
        params = "["
        bfirst = True
        for v in args:
            if bfirst:
                bfirst = False
            else:
                params += ","
            params += "\"" + v + "\""
        params += "]"
        conn.request( method, uri, body=params)
        res = conn.getresponse()
        if res.status != 200:
            log.info(" status is not 200---->" + uri)
    except Exception,e:
        log.info("--------http error-----" + ''.join(args) )
        log.info("--------http error-----" + str(e))
    finally:
        if conn:
            conn.close()
'''
def do_job( args ):
    #print ''.join(args)
    print args
'''
def main( data_dir ):
    if not check_port('127.0.0.1',770):
        print "127.0.0.1:770 is unavailable"
        log.info("127.0.0.1:770 is unavailable")
        return
    print "Server 127.0.0.1 770 is ok"
    source_name = time.strftime( '%Y%m%d',time.localtime( time.time() ) )
    source_files = ""
    need_delete_files = ""
    #merge_files = ""
    if data_dir == "ssd":
        source_files = "/data/proclog/log/storage/evicted/data/ssd/" + source_name
        #merge_files = "/data/proclog/log/storage/evicted/merge/ssd/"
        need_delete_files = "/data/proclog/log/storage/evicted/need_delete/ssd/"
    elif data_dir == "disk":
        source_files = "/data/proclog/log/storage/evicted/data/disk/" + source_name
        #merge_files = "/data/proclog/log/storage/evicted/merge/disk/"
        need_delete_files = "/data/proclog/log/storage/evicted/need_delete/disk/"
    else:
        return
    #os.system("mkdir -p "+ merge_files)
    os.system("mkdir -p "+ need_delete_files)
    split_into_small_file(source_files, need_delete_files)

    log.info("----------------complete file's operation-----------------")
    log.info("delete work start")
    work_manager = WorkManager( need_delete_files, 12 )
    work_manager.wait_allcomplete()
    log.info("complete delete work")
    print "----------------complete delete urls work------------------"

if __name__=='__main__':
    if len(sys.argv) != 2:
        print " error no data.conf"
    else:
        log_dir = sys.argv[1] + "_log/"
        log_time = time.strftime( '%Y%m%d',time.localtime( time.time() ) )
        log_name = "/data/proclog/log/storage/evicted/logs/" + log_dir + log_time
        logHandler = logging.FileHandler(log_name, 'a')
        logHandler.setLevel(logging.INFO)
        logHandler.setFormatter(formatter)
        log.addHandler(logHandler)
        main( sys.argv[1] )
