#!/usr/bin/env python
#coding: utf-8
import paramiko
class action(object):
    def __init__(self, ip, username, command):
        self.ip = ip
        self.username = username
        self.command = command
    def ssh_connect(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=self.ip, username=self.username)
            stdin,stdout,stderr=ssh.exec_command(self.command)
            print "##### > %s:%s <#####" %(self.ip, self.command)
            err_list = stderr.readlines()
            out_list = stdout.readlines()
            #print "--stderr--"
            #print err_list
            #print "--stdout--"
            #print out_list
            #print "--ssh.close--"
            ssh.close()
            return 0, err_list, out_list
        except Exception,e:
            print "####exception #####> %s:%s:%s <#####"%(self.ip, self.command, e)
            return -1,[],[]
