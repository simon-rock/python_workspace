#coding: utf-8
import svn_clone_config
import pysvn
import time, sys, string
from urlparse import urlparse
import os, urllib
import shutil
import sutil
from optparse import OptionParser
from lxml import etree as ET

g_url      = u""    #= svn_clone_config.setting['svn']          # no include "/"                远端svn地址
g_user     = ""     #= svn_clone_config.setting['user']
g_pwd      = ""     #=svn_clone_config.setting['pwd']

tmp_path   = u""    #= svn_clone_config.setting['tmp']          # no include "/"                下载文件的临时目录
local_path = u""    #= svn_clone_config.setting['local_path']   # no include "/"                本地svn副本的目录
local_svn_checkout_name = u""                                   # lcoal checkout folder name    本地svn副本的目录名字
compensation = 0                                                # 远端版本和本地版本的差值 local_version+compensation = source_version
                    #version_path = svn_clone_config.setting['reversion_path']
version    = 0      #svn_clone_config.setting['reversion']      # source svn version    上次同步的远端版本
local_version = 0                                               # local svn version     当前版本

#从配置文件获取工程信息
# xml_path  配置文件全路径
def get_config(xml_path):
    print " ----",xml_path,"----"
    global g_url
    global g_user
    global g_pwd

    global tmp_path
    global local_path
    global version
    global compensation
    
    doc = ET.parse(xml_path)
    info = doc.find('svn')
    if info != None:
        if isinstance(info.text, str):
            g_url = info.text.decode('utf8')
        else:
            g_url = info.text
        print "g_url -----", g_url#, type(g_url)
    else:
        print "need svn!"
        exit(-1)
        
    info = doc.find('user')
    if info != None:
        g_user = info.text
        print "user ------", g_user#, type(g_user)
    else:
        print "need user!"
        exit(-1)
        
    info = doc.find('pwd')
    if info != None:
        g_pwd = info.text
        print "pwd -------", g_pwd#, type(g_pwd)
    else:
        print "need pwd!"
        exit(-1)
        
    info = doc.find('tmp_path')
    if info != None:
        if isinstance(info.text, str):
            tmp_path = info.text.decode('utf8')
        else:
            tmp_path = info.text
        print "tmp_path --", tmp_path#, type(tmp_path)
    else:
        print "need tmp_path!"
        exit(-1)
        
    info = doc.find('local_path')
    if info != None:
        if isinstance(info.text, str):
            local_path = info.text.decode('utf8')
        else:
            local_path = info.text
        print "local_path ",local_path#, type(local_path)
    else:
        print "need local_path!"
        exit(-1)
        
    info = doc.find('reversion')
    if info != None:
        version = string.atoi(info.text)
        print "version ---",version#, type(version)
    else:
        print "need version!"
        exit(-1)

    info = doc.find('compensation')
    if info != None:
        compensation = string.atoi(info.text)
        print "compensation ---",compensation#, type(version)
    else:
        print "need compensation!"
        exit(-1)
        
#分析参数
def get_options(args=None):
    """setup and get options"""
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option('-f',action="store", type="string", dest="config", default="")
    #parser.add_option('-c','--threadcount',action="store",type="int", dest="thread", default=6, help="thread count")
    #parser.add_option('-m', '--delete tmp files', action="store_true", dest="clear_tmp", default=False)

    (options, other) = parser.parse_args(args)
    #if len(svg_file_specs) < 1:
    #    parser.error("Please specify the directory of the file to be processed.")

    return options, other

#获取本地版本信息，失败退出，并检验
def check_local_version():
    client = pysvn.Client()
    client.update(local_path)
    global local_svn_checkout_name
    local_svn_checkout_name = os.path.split(local_path)[-1]
    print "local_svn_checkout_name : ", local_svn_checkout_name 
    if local_svn_checkout_name == u"":
        print "local_svn_checkout_name is empty"
        exit(-1)
    entry = client.info(local_path)
    global local_version
    local_version = entry.commit_revision.number
    if local_version + compensation != version:
             print "local version path[%d]+[%d] is different from [%d]" % (local_version, compensation, version)
             exit(-1)
    return version
#        raise Exception ("")

#获取svn提交记录的 版本对应的体校信息
#start_version  本地当前版本（对应远端的版本号）
#msgs           返回 版本->提交信息的list
def get_msgs(start_version, msgs):
    client = pysvn.Client()
    list_of_revprop_names =[]
    if start_version == 0:
        msgs[0] = u'start clone'
    revision_start = pysvn.Revision(pysvn.opt_revision_kind.head)
    revision_end = pysvn.Revision(pysvn.opt_revision_kind.number, start_version)
    logs = client.log(g_url,revision_start,revision_end, limit=0)
#    logs = client.log( g_url, pysvn.Revision(pysvn.opt_revision_kind.head), \
#                pysvn.Revision(pysvn.opt_revision_kind.number, \
#                start_version, limit = 0)
    for m in logs:
        #for k in m.iterkeys():
        #    print k
        #print "---------------", m['revision'].number
        #print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(m.date))
        #print m.author
        #print m.message
        #print m.has_children
        #print m.revprops
        #print m.revision
        #print m.changed_paths
        msg = m.message
        msg += "\n-----"
        msg += str(m['revision'].number)
        msg += " "
        if m.has_key('author'):# some commit has no author
            msg += m.author
        msg += " "
        msg += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(m.date))
        #print msg.decode('utf8')  #because code is utf8 in emacs
        #print type(msg)
        #print m.message.edcode('utf8')
        #msg += m.message.decode('utf8')
        #newmsg = unicode(msg,'utf8')
        #print type(newmsg)
        #msg += m.message.encode('utf8')
        #print newmsg.encode('utf8')
        msgs[m['revision'].number] = msg.decode('utf8')

#调试用暂停
def pause_for_debug():
    print "entry any key to continue..."
    pause = raw_input()

#下载指定版本间的更新文件
#现在用于获取相邻版本间差异，并在本地提交，提交后更新配置文件中本地同步版本信息
#reversion      指定版本信息 例 1:10，现在为1:2
#msg            提交时信息，现在应为后者提交信息
#elem           配置文件的版本节点，用于更新配置文件
def download_code(reversion, msg, elem):
    print "----- process : ", reversion
    value = reversion
    url = g_url
    targetPath = tmp_path

    if string.find(value, ":") >= 0:
        (revision_min0, revision_max0) = string.split(value, ":")
        revision_min = pysvn.Revision( pysvn.opt_revision_kind.number, int(revision_min0) )
        if revision_max0 != "HEAD":
            revision_max = pysvn.Revision( pysvn.opt_revision_kind.number, int(revision_max0) )
            if int(revision_max0) <= int(revision_min0):
                print revision_max,revision_min
                raise Exception ("revision_max <= revision_min")
        hasRevision = True
    else:
        raise Exception ("Please Input revision range " + str(reversion))

    if hasRevision == False:
        raise Exception ("no find min:max  " + reversion)
#    print revision_min, revision_max
    
    urlObject = urlparse(url)
    if urlObject.scheme == 'http' or urlObject.scheme == 'https':
        if isconsole():
            url = urlObject.scheme+"://"+urlObject.netloc+urllib.quote(urlObject.path.decode(sys.stdin.encoding).encode('utf8'))
        else:
            url = urlObject.scheme+"://"+urlObject.netloc+urllib.quote(urlObject.path.encode('utf8'))

    if not url.endswith("/"):
        url = url + "/" 
    print "url", url

    client = pysvn.Client()
    summary = client.diff_summarize(url, revision_min, url, revision_max)
    for changed in summary:
        print changed['summarize_kind'], changed['path']
        # 删除操作应该记录下来，待下载完成一并操作目标svn副本
        if pysvn.diff_summarize_kind.delete == changed['summarize_kind']:
            fullPath = targetPath+"/"+changed['path']   
            if os.path.exists(fullPath):
                os.remove(fullPath)

        if pysvn.diff_summarize_kind.added == changed['summarize_kind'] or pysvn.diff_summarize_kind.modified == changed['summarize_kind']:
            if changed['node_kind'] == pysvn.node_kind.file:

                file_text = client.cat(url+urllib.quote(changed['path'].encode('utf8')), revision_max)
            
                fullPath = targetPath+"/"+changed['path']    #本地相对文件路径./Source/SurDoc/SurDoc/Advanced/CLS_DlgBackupSet.cpp
                dirPath = fullPath[0:fullPath.rfind("/")]    #本地相对文件目录./Source/SurDoc/SurDoc/Advanced
            #print fullPath
            #print dirPath
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath) # 迭代创建目录
                        
                f = open(fullPath,'wb')
                f.write(file_text)
                f.close()
            elif changed['node_kind'] == pysvn.node_kind.dir:
                fullPath = targetPath+"/"+changed['path']    #本地相对文件路径./Source/SurDoc/SurDoc/Advanced/CLS_DlgBackupSet.cpp
                if not os.path.exists(fullPath):
                    os.makedirs(fullPath) # 迭代创建目录
    #操作目标副本， 提交改变和message
    #pause = raw_input()
    sutil.copytree(tmp_path, local_path, False, True)
    update_local_clone(summary, msg)
    elem.text = str(revision_max0)
    print "----- commite success : ", reversion

#chenkin 更新到本地svn
#summary    更新的文件
#msg        更新的提交信息
def update_local_clone(summary, msg):
    changelist = []
    client = pysvn.Client()
    client.exception_style = 1
#    for changed in summary:
#        fullPath = local_path+"/"+changed['path']
#        if pysvn.diff_summarize_kind.added == changed['summarize_kind'] and changed['node_kind'] == pysvn.node_kind.dir:
#            print "added folder--", fullPath
#            client.add(fullPath)
#    for changed in summary:
    summary.reverse() 
    for changed in summary:
        fullPath = local_path+"/"+changed['path']
        changelist.append(fullPath)
        if pysvn.diff_summarize_kind.delete == changed['summarize_kind']:
            print "delete -------", fullPath
            client.remove(fullPath)
#        elif pysvn.diff_summarize_kind.added == changed['summarize_kind'] and changed['node_kind'] == pysvn.node_kind.file:
        elif pysvn.diff_summarize_kind.added == changed['summarize_kind']:
            print "added --------", fullPath
            try: 
                client.add(fullPath)
            except pysvn.ClientError, e:
                if len(e.args[1]) == 1 and e.args[1][0][1] == 150002:
                    print e.args[0]
                else:
                    raise
                    
            
        elif pysvn.diff_summarize_kind.modified == changed['summarize_kind']:
            print "modified -----", fullPath

    resu = client.checkin(changelist, msg)
    print "----- checkin to version : ", resu
    global local_version
    #---------- fun 1 ----------
    #client.update(local_path)
    #entry = client.info(local_path)
    #local_version = entry.commit_revision.number
    # ---------------------------
    #client2 = pysvn.Client()
    entry2 = client.info2(local_path, revision=pysvn.Revision( pysvn.opt_revision_kind.head ),peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ), recurse = False)
    new_revision = 0
    for name, o in entry2:
        print name, local_svn_checkout_name
        if cmp(name.decode('utf8'), local_svn_checkout_name) == 0:
            new_revision = o.rev.number
            break
    if new_revision == 0:
        print "get new version error"
        exit(-1)
    print "update local?[%d][%d]" % (local_version, new_revision)
    if local_version == new_revision:
        print "---------- update local now"
        client.update(local_path)
        new_revision = 0
        entry2 = client.info2(local_path, revision=pysvn.Revision( pysvn.opt_revision_kind.head ),peg_revision=pysvn.Revision( pysvn.opt_revision_kind.unspecified ))
        for name, o in entry2:
            if cmp(name.decode('utf8'), local_svn_checkout_name) == 0:
                new_revision = o.rev.number
                break
        if new_revision == 0:
            print "get new version error"
            exit(-1)
        if local_version == new_revision:
            print "can't update new_revision"
            exit(-1)
    else:
        local_version = new_revision
#    pause_for_debug()
    local_version = new_revision
    # ---------------------------

    print "current version : ", local_version

#根据msgs中 版本和提交信息，逐一下载更新内容，本地提交附带提交信息
#提交后清理本地临时目录
def update_by_version(xml_path, msgs):
    first = True
    start_num = 0
    log_list = sorted(msgs.iteritems(), key=lambda d:d[0], reverse = False )
    doc = ET.parse(xml_path)
    elem = doc.find("reversion")

    for v, msg in log_list:
        if first:
            start_num = v
            first = False
            continue
        s = "%d:%d" % (start_num, v)
        start_num = v
        download_code(s, msg, elem)
        doc.write(xml_path)
        sutil.removeall(tmp_path)
        #shutil.rmtree(tmp_path)
        #os.mkdir(tmp_path)
        print "----- clear tmp success : "

#判断是否为控制台运行，还是emacs 运行
def isconsole():
    if sys.stdin.encoding == None:
        return False
    else:
        return True

def main(argv = None):
    if isconsole():
        print "isconsole"
    (options, other) = get_options(argv)
    get_config(options.config)

# get version
    lversion = check_local_version()
    print "start version -----", lversion
    print "confirm start version,and entry any key to continue..."
    pause = raw_input()
# get message list
    msgs = {}
    get_msgs(lversion, msgs)
    #print msgs
# update code version by version
    update_by_version(options.config, msgs)
    
if __name__ == "__main__":
    main()
