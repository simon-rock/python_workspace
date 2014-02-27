#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import os
import shutil
import os
import glob
import sys
from stat import *

from optparse import OptionParser, SUPPRESS_HELP
# for mail
#modules for mail notification
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders
from socket import gethostname

class RunProgError(Exception):
    pass

#安全拷贝文件 重命名
def copy_file(src_path, src_file, dest_path, dest_file=None):
    if not dest_file:
        dest_file = src_file
    src = os.path.join(src_path, src_file)
    dest = os.path.join(dest_path, dest_file)
    make_writable(dest)
    if not os.path.exists(src):
        print '%s not exist' % (src)
        return
    try:
        shutil.copy(src, dest)
    except Exception, e:
        print 'copy_file, exception:', e
        raise

    make_writable(dest)
    os.rename(dst_name, "final_name")

#拷贝文件 到指定路径
def copy_file(src, dest_path, dest_file=None):
    if not dest_file:
        path, name = os.path.split(src)  #分割路径和文件名
        dest_file = name
    dest = os.path.join(dest_path, dest_file)
    if not os.path.exists(src):
        print '%s not exist' % (src)
        return
    try:
        shutil.copy(src, dest)
    except Exception, e:
        print 'copy_file, exception:', e
        raise
        
# 不存在创建文档
# 存在并且有clean标志则删除重建
def make_dir(path, clean=False):
    '''make directory'''
    if not os.path.exists(path):
        os.makedirs(path)
    elif clean:
        shutil.rmtree(path)
        os.makedirs(path)
        
#模糊查找所有匹配文件
#分割文件和后缀
def find_all_files(src):
    src_list = glob.glob(src)
    if not src_list:
        print 'Warning:can not find match files:%s' % src
    else:
        for result in src_list:
            print result
            pt, ext = os.path.splitext(result) # 分割文件名和后缀
            #pt, ext = os.path.split(result)  分割路径和文件名
            print "%s [%s]" % (pt , ext)

# 添加写标志
def make_writable(path):
    if os.path.exists(path):
        os.chmod(path, S_IWRITE)

#解压文件
def unpack_sif_special_file(src, dst):
    args = ('D:\\eworkspace\\process_data\\7z.exe', 'x', 'D:\\eworkspace\\data\\SIF_Q1_13\\NA\\04AM13100N04000SAA79.gz', '-oD:\\eworkspace')
    runprog(args)

#执行命令 等待 结果， 如果失败询问是否继续，不继续则发送邮件
def runprog(args):
    """Runs a program with the given arguments."""
    cmd = ' '.join(args)
    print 'Running', cmd

    prog_name = args[0]
    args = map(quotearg, args)
    error = 0
    try:
        error = os.spawnv(os.P_WAIT, prog_name, args)
        print '...finished...'
    except:
        print 'Error running program'
        print 'Error: %d; program: %s; args: %s' % (error, prog_name, args)
        raise

    #exit code capture, the same as error level of MS-DOS
    if 0 != error:
        err = 'ProgramName: %s\nExitCode: %d\nArgs: %s' % (prog_name, error, args[1:])
        if(ask_user_yesno(err)):
          print 'countinue...'
        else:
          #if OPTION.notify:
          if (1 == 1):
            subject = '[maps]NCDB MDC failed'
            message = 'Processing on %(host)s has halted ' \
                      'with the following error:\n\n' \
                      '%(prog)s returned %(error)d\n\n' \
                      'COMMAND: %(cmd)s'
            kwargs = {'host':hostname(),
                      'prog':prog_name,
                      'cmd':cmd,
                      'error':error}

            send_notification(subject, message, **kwargs)
          raise RunProgError(err)

#命令行有空格则 用双引号括起来
def quotearg(arg):
    """Quotes the given argument if it contains a space."""
    if ' ' in arg:
        arg = '"%s"' % arg
    return arg

#获得主机名
def hostname():
    """Returns the hostname of the machine the script is running on."""
    return gethostname()

#问用户是否停止 yes则继续， no 则停止并发邮件
def ask_user_yesno(msg):
    print '=================Error Info================='
    print msg;
    print '============================================'
    print "Do you want to continue [Yes|Y] [No|N]?\n"
    return 0
    #opt = raw_input()
    #opt = opt.upper()
    #if opt == 'YES' or opt == 'Y':
    #  return 1
    #elif opt == 'NO' or opt == 'N':
    #  return 0
    #else:
    #  ask_user_yesno('Invalid option, Please input agagin\n')

#发送邮件 内容
def send_notification(subject, formatted_msg, **kwargs):
    """Sends an email notification about the status of the Process."""
    sender = 'sigao@networksinmotion.com'
    recipients = ['sigao@networksinmotion.com']
    #sender = 'khommel@telecomsys.com'
    #recipients = ['khommel@telecomsys.com',
    #             'kiwang@telecomsys.com',
    #             'ema@telecomsys.com',
    #             'ezhao@telecomsys.com',
    #             'chunwang@telecomsys.com',
    #             'dliu@telecomsys.com',
    #             'ltang@telecomsys.com',
    #             'djtaylor@telecomsys.com',
    #             'axu@telecomsys.com']
    cc = []
    message = formatted_msg % kwargs
    sendmail(sender, recipients, cc, subject, message)

def get_options(args=None):
    """Parse command line options and parameters."""

    parser = OptionParser(add_help_option=False, usage='%prog <arg> [option]', description="")

    parser.add_option('-c', '--config', action='store', default="ncdbconfig.xml", dest='config', help='ncdb configuration files')
    parser.add_option('-b', '--begin',action='store', type='int', default=0, dest='begin', help='begin step')
    parser.add_option('-e', '--end',action='store', type='int', default=-1, dest='end', help='end step')
    parser.add_option('-n', '--notify', dest='notify', action='store_true',
                      default=False, help='notify by mail or not')
    parser.add_option('-p', '--polygons only', action="store_true", dest='poly', default=False)
    parser.add_option('-a', '--pointaddr only', action="store_true", dest='pointaddr', default=False)
    parser.add_option('-h', '--help', dest='help', action='store_true', default=False)

    global HELP
    HELP = parser.format_help().strip()
    options, args = parser.parse_args(args)
    print HELP
    return options, args

#发送邮件
def sendmail(fromaddr, toaddrs, bccaddrs, subject, body, attach=[]):
    """Send an email message with the given parameters using SMTP."""
    smtpserver = 'mx0.networksinmotion.com'

    # Create a Multipart email message.
    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = ','.join(toaddrs)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['cc'] = ','.join(bccaddrs)
    message.attach(MIMEText(body))

    # Attach the given file attachments to the email.
    for attachment in attach:
        if not os.path.exists(attachment):
            continue  # Skip files that don't exist.
        fname = os.path.basename(attachment)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attachment, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="%s"' % fname)
        message.attach(part)

    # Create an SMTP object with the outbound email server (SMTP).
    server = smtplib.SMTP(smtpserver)

    # Start the conversation with EHLO.
    server.ehlo()

    # Send the email.
    server.sendmail(fromaddr, toaddrs, message.as_string())

    # Close the connection.
    server.close()

# 遍历目录处理操作
# indir      当前目录
# out        当前输出目录
# handle_folder_process 处理目录方法，通常是自己自己
# handle_file_process   处理文件方法
# build_tree 是否构建相同的目录树
def traverse_handle(indir, out, handle_folder_process, handle_file_process, build_tree = True):
    make_dir(out)
    for o in os.listdir(indir):
        o_path = os.path.join(indir, o)
        if build_tree:
            o_out = os.path.join(out, o)
        else:
            o_out = out
        if os.path.isdir(o_path):            
            handle_folder_process(o_path, o_out, handle_folder_process, handle_file_process, build_tree)
        if os.path.isfile(o_path):
            handle_file_process(o_path, out)

def handle_file_process(in_file, out_path): #    def landmark_process(file, out):
#    print "[", file, "]  ==>>  [", out,"]"
    if file.endswith("obj.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        args = [gzout, '-d', out]
        obj2bin.main(args)
        path, filename = os.path.split(gzout)
        pt, ext = os.path.splitext(filename)
        if not lm_table.has_key(pt):
            lm_table[pt] = ",0,0\n"
        #table_path = os.path.join(out, "landmark_table.txt")
        #fp = open(table_path, "a")
        #fp.write("%s,,0,0\n"%pt)
        #fp.close()
    elif file.endswith("jpg.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        png_path = gzout.replace(".jpg", ".PNG")
        path, filename = os.path.split(png_path)
        png_path = os.path.join(out, TEMP_PNG,filename)
        args = [CONVERT, gzout, png_path]
        runprog(args)
    elif file.endswith("png.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        png_path = gzout.replace(".png", ".PNG")
        path, filename = os.path.split(png_path)
        png_path = os.path.join(out, TEMP_PNG,filename)
        args = [CONVERT, gzout, png_path]
        runprog(args)
    elif file.endswith("_link.xml.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        load_landmark_reference_point(gzout)
        
#解压文件 gz
def ungzip(gzfile, outfile):
    "I think unzip if need"
    f = gzip.open(gzfile)
    uf = open(outfile, "wb")
    data = f.read()
    uf.write(data)
    uf.close()
    f.close()

# ============== test ================
# 拷贝函数测试
def test_copy():
    copy_file("./data", "src.txt", "./data", "tar.txt")
    find_all_files(r"D:\eworkspace\data\SIF_Q1_13\NA\04*[.sif|.gz]")

# 测试执行命令,失败询问是否继续，不继续，发送邮件

def test_runprog():
    args = ('D:\\eworkspace\\process_data\\7z.exe', 'Xx', 'D:\\eworkspace\\data\\SIF_Q1_13\\NA\\04AM13100N04000SAA79.gz', '-oD:\\eworkspace')
    runprog(args)

def test_other():
    #写文件
    last_run_log = open('lastrun.log', 'w')
    last_run_log.write(begin + '\n')
    last_run_log.flush()
    last_run_log.close()

    #获得运行目录
    os.getcwd()
    
    #改变程序工作目录
    os.chdir("c:")

def test_getoption(argv = None):
    (options, argv) = get_options(argv)
    svg_files = list(file for file_spec in argv for file in glob.glob(argv))
    global OPTION
    OPTION = options
    if options.help:
        print HELP
if __name__ == "__main__":
    test_getoption()

