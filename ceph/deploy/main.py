#!/usr/bin/env python
#coding: utf-8

from remotecmd import action
import commands
import os
hostname = "cephnode5"
username = "root"
localhost = "localhost"
def install_first_mon(hostname, ip, public_net, cluster_net):
    print hostname, ip, public_net, cluster_net

def add_osd_to_pool(osd_id, pool, datacenter_id, rack_id, host_id):
   cmd = "ceph osd crush create-or-move --name=osd."+osd_id+" -- "+osd_id+" 1 "
   cmd += "root="+pool+"-root "
   cmd += " datacenter="+pool+"-"+datacenter_id
   cmd += " rack="+pool+"-"+rack_id
   cmd += " host="+pool+"-"+host_id
   print cmd 
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   if s != 0:
      return -1
   return 0
   
    
def remove_osd_from_pool(osd_id):
   osd_id = raw_input("write your osd_id:")
   ''' '''
   cmd = "ceph osd crush remove osd." + osd_id
   print cmd
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   ret_out = "removed item id "+osd_id+" name 'osd."+osd_id+"' from crush map"
   print ret_out
   if s == 0 and o == ret_out:
      return 0
   return -1
   #conn = action(localhost,username,command) 
   #ret, el, ol = conn.ssh_connect()
   #print "--",command,"-----",ret, el, ol
   #if ret < 0:
   #   return ret
   #for e in el:
   #   if e.find("removed item id "+osd_id+" name 'osd."+osd_id+"' from crush map") > 0:
   #      return 0
   #return -1

def del_rule(pool):
   cmd = "ceph osd crush rule rm "+pool+"-rule"
   print cmd
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   if s == 0 and o == "":
      return 0
   return -1

def create_rule(pool, replicate_type):
   cmd = "ceph osd crush rule create-simple "+pool+"-rule "+pool+"-root "+replicate_type+" firstn"
   print cmd
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   if s == 0 and o == "":
      return 0
   return -1

def create_pool(pool, pg_num):
   cmd = "ceph osd pool create "+pool+"  "+pg_num+" "+pg_num+" replicated "+pool+"-rule"
   print cmd
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   if s == 0 and o.find("created")>0:
      return 0
   return -1
    
def del_pool(pool):
   cmd = "ceph osd pool rm "+pool+" "+pool+" --yes-i-really-really-mean-it"
   print cmd
   s,o = commands.getstatusoutput(cmd)
   print s,"---",o
   if s == 0 and o.find("removed")>0:
      return 0
   return -1
   
def create_osd(host, data_dev, journal_part):
   command = "ceph-disk list | grep " + dev + " | grep osd." + osd_id
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect()
   print "--",command,"-----",ret, el, ol, len(ol) 

def destroy_osd(host, dev, osd_id):
   host = raw_input("write your host:")
   dev = raw_input("write your dev:")
   osd_id = raw_input("write your osd_id:")
   ''''''
   command = "ceph-disk list | grep " + dev + " | grep osd." + osd_id
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect() 
   print "--",command,"-----",ret, el, ol, len(ol)
   if ret < 0 or len(ol) != 1:
      return -1

   command = "systemctl stop ceph-osd@"+osd_id
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect()
   print "--",command,"-----",ret, el, ol

   command = "ceph-disk destroy --destroy-by-id "+osd_id
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect()
   print "--",command,"-----",ret, el, ol
   if ret < 0 or len(el) or len(ol):
      return -1

   command = "mv /var/lib/ceph/osd/ceph-"+osd_id+"/magic /var/lib/ceph/osd/ceph-"+osd_id+"/magic.last"
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect()
   print "--",command,"-----",ret, el, ol
   if ret < 0 or len(el):
      return -1

   command = "umount /dev/"+dev+"1"
   conn = action(host,username,command)
   ret, el, ol = conn.ssh_connect()
   print "--",command,"-----",ret, el, ol
   if ret < 0 or len(el):
      return -1
   return 0 


def test_remotecmd(argv = None):
    hostname = raw_input("write your hostname:")
    username = raw_input("write your username:")
    command = raw_input("write your excute command:")
    print hostname
    conn = action(hostname,username,command)
    ret,el,ol= conn.ssh_connect()
    print "--",command,"-----",ret, el, ol

if __name__ == "__main__":
    #test_remotecmd()
    os.chdir("/etc/ceph")
    #install_first_mon("cephnode5", "10.210.0.70", "10.210.0.0/24", "10.210.0.0/24")
    #ret = remove_osd_from_pool("-1")
    ret = destroy_osd("cephnode3", "sdg", "9")
    #osd_id, pool, datacenter_id, rack_id, host_id
    #ret = add_osd_to_pool("8", "pool1", "datacenter_1", "rack_1", "host1")
    #ret = create_rule("pool-pool1","rack")
    #ret = del_rule("pool1")
    #ret = create_pool("pool-pool1", "10")
    #ret = del_pool("pool-pool1")
    print ret
