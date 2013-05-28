#
# (C) Copyright 2010 by TeleCommunication Systems, Inc.
#
# The information contained herein is confidential, proprietary
# to TeleCommunication Systems, Inc., and considered a trade secret as
# defined in section 499C of the penal code of the State of
# California. Use of this information by anyone other than
# authorized employees of TeleCommunication Systems is granted only
# under a written non-disclosure agreement, expressly
# prescribing the scope and manner of such use.
#
# author: senwang
# date:   05/24/2011
# revision for TomTom data processing 8/12/2012

from optparse import OptionParser, SUPPRESS_HELP
import ConfigParser
import glob
import os.path
import os
import sys
import shutil
import gzip
import xml.etree.ElementTree as ET
from stat import *
from types import *

#modules for mail notification
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders
from socket import gethostname

#default configuration filename
CONFIG_NAME = 'ncdbconfig.xml'

#define constant for data source type
ST_UNKNOWN = 0 #unknown data source
ST_NT = 1 #Navteq data source
ST_TA = 2 #Tomtom data source

class PostProcessOptions:
    '''PostProcess Options class'''

    def __init_(self):
      '''class initialize method'''

      self.outpath = None
      self.flat = False
      self.pktproc = False
      self.resrcproc = False
      self.resrcpath = None

    def load(self, options_node):
      '''load configuration file'''
      if None != options_node:
          self.flat = (options_node.attrib['flat_mode'].upper() == 'TRUE')
          self.pktproc = (options_node.attrib['package'].upper() == 'TRUE')
          self.resrcproc = (options_node.attrib['resource_needed'].upper() == 'TRUE')
          self.outpath = os.path.abspath(options_node.find('outpath').text)
          if self.resrcproc:
            self.resrcpath = os.path.abspath(options_node.find('resource_dir').text)

class ConfigReader:
    '''configuration reader'''

    def __init__(self, cfgname):
        '''class initialize method'''
        self.name = cfgname
        self.input = None
        self.unpack_dir = None
        self.output = None
        self.existing_map_path = None
        self.region = None
        self.set_ids = []
        self.paths = {}
        self.dici = {}
        self.st = ST_NT;

        self.postopt = PostProcessOptions()

        self.ow_path = None
        self.nf_path = None

        self.pkgoutdir = None
        self.resrcdir = None

        #options
        self.do_dici = False
        self.do_outer_ploygon = False
        self.for_hybrid = False
        self.do_pointaddr = False
        self.load()

        pass

    def load(self, ):
        '''load configuration file'''
        doc = ET.parse(self.name)
        source = doc.getroot().attrib['source'].upper()
        if source == 'TA':
            self.st = ST_TA
        elif source == 'NT':
            self.st = ST_NT
        else:
            self.st = ST_UNKNOWN

        process_node = doc.find(r'process')
        if None != process_node:
            self.input = process_node.attrib['input']
            self.unpack_dir = process_node.get('unpack_dir')
            if None != self.unpack_dir:
              self.unpack_dir = os.path.abspath(self.unpack_dir)
            self.output = os.path.abspath(process_node.attrib['output'])
            self.existing_map_path = process_node.get('existing_map_path')
            self.region = process_node.attrib['region']
            self.set_ids = process_node.attrib['set_id'].split(' ')

        options_node = doc.find('options')
        if None != options_node:
            self.do_dici = (options_node.attrib['do_dici'].upper() == 'TRUE')
            self.do_outer_ploygon = (options_node.attrib['do_outer_world_polygon'].upper() == 'TRUE')
            self.for_hybrid = (options_node.attrib['for_hybrid'].upper() == 'TRUE')
            self.post_proc = (options_node.attrib['post_proc'].upper() == 'TRUE')
            self.do_lane_guidance = (options_node.attrib['do_lane_guidance'].upper() == 'TRUE')
            self.do_pointaddr = (options_node.get('do_pointaddr', 'false').upper() == 'TRUE')

        if self.do_outer_ploygon:
            polygons_node = doc.find('polygons')
            if None != polygons_node:
                self.ow_path = polygons_node.find('owpath').text
                self.nf_path = polygons_node.find('nfpath').text

        if self.post_proc:
            postopt_node = doc.find('post_process')
            if None != postopt_node:
                self.postopt.load(postopt_node)

        for id in self.set_ids:
            xpath = 'asset/regions/%s/%s' % (self.region, id)
            id_node = doc.find(xpath)
            if None != id_node:
                keys = id_node.text.split(' ')
                set_id = id_node.tag
                path = id_node.get('path', '')
                prod = int(id_node.get('prodtype', '0'))

                #self.paths.append((keys, prod + '/' + path))
                self.paths[set_id] = (keys, path, prod)

        #parse DiCi
        xpath = 'asset/DiCi/%s' % (self.region)
        subdcas = doc.find(xpath)
        if subdcas:
          for dca in subdcas:
            id = dca.attrib['id']
            files = dca.text.split(' ')
            self.dici[id] = files

        #print self.dici
        print 'Process datasource is %s' % source
        print self.paths

    def get_input_dir(self):
        return self.input

    def get_unpack_dir(self):
      if self.unpack_dir:
        return self.unpack_dir
      else:
        return self.output

    def get_output_dir(self):
        return self.output

    def get_existing_map_path_dir(self):
      if self.existing_map_path:
        return self.existing_map_path
      else:
        print 'Warning: cannot fine existing_map_path in config file'
        return ''

    def get_region(self):
        return self.region

    def get_set_ids(self):
        return self.set_ids

    def get_paths(self):
        return self.paths

class PathManager:
    '''path manager'''

    def load_cfg(self, cfg_name):
        self.configrd = ConfigReader(cfg_name)
        self.path_tools = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.abspath(self.configrd.get_output_dir())

    def get_cfg(self):
        return self.configrd

    def get_region(self):
        return self.configrd.region

    def get_tools_path(self):
        return self.path_tools

    def get_input_root_dir(self):
        return self.configrd.get_input_dir()

    def get_dici_map(self):
      return self.configrd.dici

    def get_output_dir(self):
        return self.output_dir

    def get_maps_dir(self):
        return os.path.join(self.output_dir,'maps')

    def get_dici_dir(self):
        return os.path.join(self.output_dir,'maps', 'dici')

    def get_sif_dir(self):
        sif = 'sif'
        if ST_TA == self.configrd.st:
            sif = 'shp'
        return os.path.join(self.configrd.get_unpack_dir(),sif)

    def get_data_input_dirs(self):
        return self.configrd.get_paths()

    def get_source_data_path(self):
        return os.path.join(self.configrd.get_input_dir(), self.configrd.region)
				
    def get_existing_map_path_dir(self):
        return self.configrd.get_existing_map_path_dir()

#===================================================
#utility functions
#===================================================
class RunProgError(Exception):
  pass

def hostname():
    """Returns the hostname of the machine the script is running on."""
    return gethostname()

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


def send_notification(subject, formatted_msg, **kwargs):
    """Sends an email notification about the status of the Process."""
    sender = 'khommel@telecomsys.com'
    recipients = ['khommel@telecomsys.com',
                 'kiwang@telecomsys.com',
                 'ema@telecomsys.com',
                 'ezhao@telecomsys.com',
                 'chunwang@telecomsys.com',
                 'dliu@telecomsys.com',
                 'ltang@telecomsys.com',
                 'djtaylor@telecomsys.com',
                 'axu@telecomsys.com']
    cc = []
    message = formatted_msg % kwargs
    sendmail(sender, recipients, cc, subject, message)

def quotearg(arg):
    """Quotes the given argument if it contains a space."""
    if ' ' in arg:
        arg = '"%s"' % arg
    return arg

def ask_user_yesno(msg):
    print '=================Error Info================='
    print msg;
    print '============================================'
    print "Do you want to continue [Yes|Y] [No|N]?\n"
    opt = raw_input()
    opt = opt.upper()
    if opt == 'YES' or opt == 'Y':
      return 1
    elif opt == 'NO' or opt == 'N':
      return 0
    else:
      ask_user_yesno('Invalid option, Please input agagin\n')

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
          if OPTION.notify:
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


def make_dir(path, clean=False):
    '''make directory'''
    if not os.path.exists(path):
        os.makedirs(path)
    elif clean:
        shutil.rmtree(path)
        os.makedirs(path)

def create_directories(directory_list):
    """Creates each directory in the list if it does not exist."""
    for directory in directory_list:
        if not os.path.exists(directory):
            print 'makedirs:', directory
            os.makedirs(directory)


def rename_directories(directory_list):
    """Renames each directory in the list by appending a timestamp."""
    timestamp = time.strftime('%y%m%d-%H%M')
    for directory in directory_list:
        if os.path.exists(directory):
            saved_dir = '%s.%s' % (directory.rstrip(os.sep), timestamp)
            try:
                os.rename(directory, saved_dir)
            except OSError:
                print 'ERROR: Cannot rename %s.' % directory
                print 'Make sure all files in the directory are closed.'
                sys.exit()


def remove_directories(directory_list):
    """Removes each directory in the list."""
    for directory in directory_list:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
            except OSError:
                print 'ERROR: Cannot delete %s.' % directory
                print 'Make sure all files in the directory are closed.'
                sys.exit()


def empty_dir(path):
    """Delete all files in the given directory."""
    for filename in os.listdir(path):
        del_path = os.path.join(path, filename)
        if os.path.isfile(del_path):
            try:
                os.remove(del_path)
            except Exception, e:
                print 'empty_dir, exception:', e
                raise


def remove_file(path):
    """If the path/file exists and is a file, delete it."""
    if os.path.exists(path) and os.path.isfile(path):
        try:
            os.remove(path)
        except Exception, e:
            print 'remove_file, exception:', e
            raise


def make_writable(path):
    if os.path.exists(path):
        os.chmod(path, S_IWRITE)


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

def copytree(src, dst):
    """Recursively copy a directory tree using copy2().
    Modified from shutil.copytree
    """
    base = os.path.basename(src)
    dst = os.path.join(dst, base)
    names = os.listdir(src)
    if not os.path.exists(dst):
        os.mkdir(dst)
    for name in names:
        srcname = os.path.join(src, name)
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dst)
            else:
                copy_file(src, name, dst)
        except:
            raise

def rename_file(src_path, src_file, dest_file):

    src = os.path.join(src_path, src_file)
    dest = os.path.join(src_path, dest_file)
    if not os.path.exists(src):
        print '%s not eixts' % (src)
        return
    if os.path.exists(dest):
        os.remove(dest)

    os.rename(src, dest)

def move_file(src_path, src_file, dest_path, dest_file=None):
    if not dest_file:
        dest_file = src_file
    src = os.path.join(src_path, src_file)
    dest = os.path.join(dest_path, dest_file)
    make_writable(dest)
    if not os.path.exists(src):
        print '%s not exist' % (src)
        return

    if os.path.exists(dest):
        try:
            os.remove(dest)
        except Exception, e:
            print 'move_file (remove), exception:', e
    try:
        os.rename(src, dest)
    except Exception, e:
        print 'move_file (rename), exception:', e
        raise

    make_writable(dest)

#===================================================
#phase1 steps
#===================================================
def make_TA_output_dir():
    '''create output directory'''
    #print 'Processing step:', sys._getframe().f_code.co_name
    #prapare proper admintypes.xml
    copy_file(path_mgr.get_tools_path(), 'admintypesTA.xml',
            path_mgr.get_tools_path(), 'admintypes.xml')


    #make sif
    make_dir(path_mgr.get_sif_dir())

    #makd dirs
    make_dir(os.path.join(path_mgr.get_sif_dir(), 'shpd'))
    make_dir(os.path.join(path_mgr.get_sif_dir(), '2dcm'))
    make_dir(os.path.join(path_mgr.get_sif_dir(), 'poi'))


    #make maps
    root = path_mgr.get_output_dir()
    make_dir(root)
    make_dir(os.path.join(root, 'maps'))

    #make maps/dici
    make_dir(os.path.join(root, 'maps', 'dici'))

    #make maps/dici/merged
    make_dir(os.path.join(root, 'maps', 'dici', 'merged'))


    #make maps/dici
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'maps'))
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'shrunk'))
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'shrunk', 'maps'))

def make_NT_output_dir():
    '''create output directory'''
    #print 'Processing step:', sys._getframe().f_code.co_name
    #prapare proper admintypes.xml
    copy_file(path_mgr.get_tools_path(), 'admintypesNT.xml',
            path_mgr.get_tools_path(), 'admintypes.xml')

    #make sif
    make_dir(path_mgr.get_sif_dir())

    #make maps
    root = path_mgr.get_output_dir()
    make_dir(root)

    make_dir(os.path.join(root, 'maps'))

    #make maps/dici
    make_dir(os.path.join(root, 'maps', 'dici'))

    #make maps/dici/merged
    make_dir(os.path.join(root, 'maps', 'dici', 'merged'))


    #make maps/dici
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'maps'))
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'shrunk'))
    make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'shrunk', 'maps'))

def make_output_dir():
    if path_mgr.get_cfg().st == ST_NT:
        make_NT_output_dir()
    elif path_mgr.get_cfg().st == ST_TA:
        make_TA_output_dir()

def get_tool_path(name):
    return os.path.join(path_mgr.get_tools_path(), name)

def enter_work_dir(path):
    cwd = os.getcwd()
    os.chdir(path)
    return cwd

def extract_sif(src, dst):
    '''Extracts the source GZ file to the destination SIF file.'''
    print src
    path, name = os.path.split(src)
    final_name = os.path.join(dst, 'sif.dat')

    if not os.path.exists(final_name):
        gz_file = gzip.GzipFile(src, 'rb')
        out = open(final_name, 'wb')
        out.writelines(gz_file)
        out.close()
        gz_file.close()

def unpack_sif_special_file(src, dst):

    print src
    path, name = os.path.split(src)
    dst_name = os.path.join(dst, name[0:-3])
    final_name = os.path.join(dst, 'sif.dat')

    if not os.path.exists(final_name):
        #unpack
        args = (get_tool_path('7z.exe'), 'x', src, '-o'+dst)
        runprog(args)

        #rename
        os.rename(dst_name, final_name)

def unpack_shape_special_file(src, dst):

    print src
    path, name = os.path.split(src)
    dst_name = os.path.join(dst, name[0:-3])

    if not os.path.exists(dst_name):
        #unpack
        args = (get_tool_path('7z.exe'), 'x', src, '-o'+dst)
        runprog(args)

def sifsplit():

    cwd = os.getcwd()
    source_path = path_mgr.get_source_data_path()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = '%s/%s/%s*[.sif|.gz]' % (source_path, country, key)
            src_list = glob.glob(src)
            if not src_list:
                print 'Warning:can not find match files:%s' % src
                continue;
            src = src_list[0]
            dst = os.path.join(path_mgr.get_sif_dir(), key)
            make_dir(dst)

            #unpack files
            pt, ext = os.path.splitext(src)
            if ext == '.gz':
                unpack_sif_special_file(src, dst)
            else:
                extract_sif(src, dst)

            #run sifsplit.exe
            os.chdir(dst)

            args = (os.path.join(path_mgr.get_tools_path(), 'sifsplit.exe'), 'sif.dat')
            runprog(args)
            os.remove(os.path.join(dst, 'sif.dat'))

    os.chdir(cwd)

def tasplit():

    cwd = os.getcwd()
    #products = ['mn', 'li', '2dcm', 'mnvmipa']
    inoutmaps = [
                    ('mn', 'shpd'),
                    ('li', 'shpd'),
                    ('2dcm', '2dcm'),
                    ('mnvmipa', 'shpd'),
                    ('mnap', 'shpd'),
                ]

    source_path = path_mgr.get_source_data_path()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
      for key in keys:
        for io in inoutmaps:
            print io
            if io[0] == '2dcm':
                src = '%s/%s/%s/%s/*/*[pxf].gz' % (source_path, io[0], country, key)
            elif io[0] == 'mnvmipa':
              src = "%s/%s/%s/%s/*[nfp][eat].txt.gz" % (source_path, io[0], country, key)
            else:
                src = '%s/%s/%s/%s/*[pxf].gz' % (source_path, io[0], country, key)
            src_list = glob.glob(src)
            if not src_list:
                print 'Warning:can not find match files:%s' % src
                continue;

            dst = os.path.join(path_mgr.get_sif_dir(), io[1], country, key)
            make_dir(dst)

            for file in src_list:
            #unpack files
                unpack_shape_special_file(file, dst)

    os.chdir(cwd)

def proc_one_dici(src, dst, key):
    """If we have DiCi data, copy it to the subdca directories."""

    dest_dir = os.path.join(dst, 'DiCi')
    make_dir(dest_dir, True)

    for xml_file in path_mgr.get_dici_map()[key]:
      xml_path = os.path.join(src, 'DiCi', xml_file + '.gz')
      if os.path.exists(xml_path):
        #unpack
        args = (get_tool_path('7z.exe'), 'x', xml_path, '-o'+dest_dir)
        runprog(args)

        # Call DiCiParse from the DiCi directory.
        os.chdir(dest_dir)
        args = (get_tool_path('DiCiParse.exe'),)
        runprog(args)

def proc_dici():

    exec_name = 'DiCiParse.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)

            if key in path_mgr.get_dici_map().keys():
              #unzip
              proc_one_dici(path, src, key)

    os.chdir(cwd)

def sif2raw():

    exec_name = 'sif2raw.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)

            args = (os.path.join(path_mgr.get_tools_path(), exec_name), '0', '0', '0', '0', dst, '0','-lights','-signs')
            runprog(args)

    os.chdir(cwd)

def sif2polygon():

    exec_name = 'sif2rawpolygon.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in  path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)

            args = [os.path.join(path_mgr.get_tools_path(), exec_name), '-i','.', '-o', dst, '-t', 'p', '-c']
            # Workaround for MEX.
            if key in ('06', '07', '08', '09'):
                args.append('1')
            else:
                args.append('0')

            runprog(args)

    os.chdir(cwd)

def sif2buildings():

    exec_name = 'sif2rawpolygon.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in  path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)

            args = (os.path.join(path_mgr.get_tools_path(), exec_name), '-i','.', '-o', dst, '-m', '-t', 'b')
            runprog(args)

    os.chdir(cwd)


def sif2poi():

    #exec_name = 'sif2rawpoi.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in  path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)

            opts = [(os.path.join(path_mgr.get_tools_path(), 'sif2rawpoi.exe'), '.', dst),]
            if path_mgr.get_cfg().for_hybrid:
                opts.append((os.path.join(path_mgr.get_tools_path(), 'sif2rawnewpoi.exe'), '-raw', '-i',src, '-o', dst))

            [runprog(param) for param in opts]e

    os.chdir(cwd)

def sif2rawlaneinfo():
    '''sif2laneinfo'''
    exec_name = 'sif2rawlaneinfo.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in  path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)
            os.chdir(src)
            args = (os.path.join(path_mgr.get_tools_path(), exec_name), '.', dst, '-m:CLM')
            runprog(args)

    os.chdir(cwd)

def ta2raw():

    exec_name = 'ta2raw.exe'
    cwd = os.getcwd()
    base_id = 10000000
    source_path = path_mgr.get_source_data_path()
    linkids_map = {}
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            if key == 'c71' or key == 'chn':
              continue
            linkids_map[base_id] = (country, key)
            src = os.path.join(path_mgr.get_sif_dir(), 'shpd', country)

            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)
            print os.getcwd()
            
            args = [os.path.join(path_mgr.get_tools_path(), exec_name), country, key, str(base_id), '-pt', str(prodtype),
                    '-o', path_mgr.get_dici_dir()+('\\'), '-sl']
            #New Zealand and Australia don't need shift from [170, 180] to [-190, -180]
            #if country in ['NZL', 'AUS'] or path_mgr.get_region() == :
            if path_mgr.get_region() in ['AP', 'AU'] or country in ['RUS']:
              args.append('-ns')
            
            #need do generalization when process Phillipines
            if country in ['PHL']:
              args.append('-thin')
              
            runprog(args)

            base_id = base_id + 10000000

    #write linkids.manf
    manf_name = os.path.join(path_mgr.get_dici_dir(), 'linkids.manf')
    manf = open(manf_name, 'w')
    manf.write('Total Dataset: %s\n' % len(linkids_map))
    manf.write('Start Link ID|Country|Dataset\n')
    
    keys = list(linkids_map.keys())
    keys.sort()
    for key in keys:
      manf.write('%10s|%3s|%3s\n' % (key, linkids_map[key][0], linkids_map[key][1]))
    manf.close()
      
    os.chdir(cwd)

def ta2raw_pointaddr():

    exec_name = 'TA2RawPointAddr.exe'
    cwd = os.getcwd()
    base_id = 10000000
    source_path = path_mgr.get_source_data_path()
    linkids_map = {}
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), 'shpd', country)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)
            os.chdir(src)

            #process point address files
            file_prefix = r'%s\%s%s___________' % (key, country, key)
            args = [os.path.join(path_mgr.get_tools_path(), exec_name),
                    os.path.join(src , file_prefix), dst]
            runprog(args)
 
def ta2polygon():
    #..\..\..\..\Shapefile2RawPoly ..\..\..\..\TeleAtlas.cfg %3\%2%3___________ ..\..\..\maps\dici\%3 p

    BASE_ID_MAP = \
    {
        'NA' : (10000000, 2000000),
        'EU' : (1000000000, 1500000),
        'AP' : (2000000000, 1000000),
        'SA' : (2500000000, 1000000),
        'AU' : (3000000000, 1000000),
        'AF' : (3500000000, 1000000),
        'ME' : (4000000000, 1000000)
    }
    
    region = path_mgr.get_cfg().get_region().upper();
    assert(BASE_ID_MAP.has_key(region))
    
    (base_id, step) = BASE_ID_MAP.get(region)
    print 'BaseID %d, Step: %d' % (base_id, step)
    
    #base_id = 10000000
    exec_name = 'Shapefile2RawPoly.exe'
    cwd = os.getcwd()
    source_path = path_mgr.get_source_data_path()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:

            #process shpd
            src = os.path.join(path_mgr.get_sif_dir(), 'shpd', country)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            os.chdir(src)

            #process polygon files
            file_prefix = r'%s\%s%s___________' % (key, country, key)
            args = [os.path.join(path_mgr.get_tools_path(), exec_name),
                    os.path.join(path_mgr.get_tools_path(), 'TeleAtlas.cfg'), file_prefix, dst,'p', '-pt', str(prodtype), '-baseid', str(base_id)]
            runprog(args)

            base_id = base_id + step
            #process 2dcm
            src = os.path.join(path_mgr.get_sif_dir(), '2dcm', country, key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(src)

            #processing buildings
            #file_prefix = r'2dcm\%s\%s\\' % (country, key)
            #for Sensis data, we should obtain building from landuse layer
            if prodtype == 3:
                args = [os.path.join(path_mgr.get_tools_path(), exec_name),
                      os.path.join(path_mgr.get_tools_path(), 'TeleAtlas4SensisBldg.cfg'), file_prefix, dst,'b', '-baseid', str(base_id)]
            else:
                os.chdir(src)
                args = [os.path.join(path_mgr.get_tools_path(), exec_name),
                      os.path.join(path_mgr.get_tools_path(), 'TeleAtlas2d.cfg'), '.\\', dst,'b', '-baseid', str(base_id)]

            runprog(args)
            base_id = base_id + step

    os.chdir(cwd)

def ta2poi():
    #..\..\..\..\TA2RawPoi %3 %2%3 ..\..\..\..\TAPoiTypeDict.xml ..\..\..\maps\dici\%3\
    cwd = os.getcwd()
    source_path = path_mgr.get_source_data_path()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            #process poi
            if key == 'c71' or key == 'chn':
               continue
            src = os.path.join(path_mgr.get_sif_dir(), 'poi', 'chn')
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            make_dir(dst)

            #copy ax.dbf to poi dir
            cpSrc = os.path.join(path_mgr.get_sif_dir(), 'shpd', 'chn', key)
            cpDst = os.path.join(path_mgr.get_sif_dir(), 'poi', 'chn', key)
            copy_file(cpSrc, 'chn'+key+'___________a0.dbf', cpDst)
            copy_file(cpSrc, 'chn'+key+'___________a1.dbf', cpDst)
            copy_file(cpSrc, 'chn'+key+'___________a8.dbf', cpDst)
            copy_file(cpSrc, 'chn'+key+'___________a9.dbf', cpDst)

            os.chdir(src)
            args = [os.path.join(path_mgr.get_tools_path(), 'TA2RawPoi.exe'), key, 'chn'+key,
                    os.path.join(path_mgr.get_tools_path(), 'TAPoiTypeDict.xml'), '..\\..\\..\\maps\\dici\\'+key+'\\']
            #runprog(args)

            #copy poi.txt to dst dir
            root = path_mgr.get_output_dir()
            make_dir(os.path.join(root, 'maps', 'dici', 'merged', 'shrunk', 'maps', 'gdf', key))
            poiDir = os.path.join(path_mgr.get_dici_dir(), 'merged\\shrunk\\maps\\gdf\\', key)
            copy_file(dst, 'poi.txt', poiDir)

    os.chdir(cwd)

def make_stitch_cfg(cfg_name, more=[], ignorekeys = False, forpolygon = False):

    #generate configuration files: Test.in
    cfg = open(cfg_name, 'w')

    if not ignorekeys:
        for keys, country, prodtype in path_mgr.get_data_input_dirs().itervalues():
            if forpolygon and (prodtype == 4):
                continue
            for key in keys:
                if forpolygon == False and (key == 'c71' or key == 'chn'):
                    continue
                cfg.write(key)
                cfg.write('\n')


    if more:
        cfg.write('\n'.join(more))
        cfg.write('\n')

    cfg.write('$')
    cfg.close()

def is_only_one_subdca(forpolygon = False):
    subDcas = []
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            if forpolygon and (prodtype == 4):
                continue
            subDcas.append(key)

    if len(subDcas) == 1:
        return (True, subDcas[0])
    else:
        return (False, None)

def stitch():

    exec_name = 'stitch.exe'
    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())

    (only_one, subDca) = is_only_one_subdca()

    if only_one:
        #not call stitch.exe, copy data to merge directory
        src = os.path.join(path_mgr.get_dici_dir(), subDca, '')
        dst = os.path.join(path_mgr.get_dici_dir(), 'merged')
        copytree(src, dst)

    else:
        cfg_name = 'Link.in'
        make_stitch_cfg(cfg_name, [])

        ops = ([os.path.join(path_mgr.get_tools_path(), 'stitch.exe'), cfg_name, '.'],)
        if path_mgr.get_cfg().for_hybrid:
            ops.append((os.path.join(path_mgr.get_tools_path(), 'poistitcher.exe'), cfg_name, '.'))

        if path_mgr.get_cfg().do_pointaddr:
          ops[0].append('-TT')
          
        [runprog(param) for param in ops]

        os.chdir(cwd)
				
def stitch_pointaddr():

    exec_name = 'stitch.exe'
    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())

    (only_one, subDca) = is_only_one_subdca()

    if only_one:
        #not call stitch.exe, copy data to merge directory
        src = os.path.join(path_mgr.get_dici_dir(), subDca, '')
        dst = os.path.join(path_mgr.get_dici_dir(), 'merged')
        copytree(src, dst)

    else:
        cfg_name = 'Link.in'
        make_stitch_cfg(cfg_name, [])

        ops = ([os.path.join(path_mgr.get_tools_path(), 'stitch.exe'), cfg_name, '.', '-f', 'pointaddr.raw', '-TT'],)
          
        [runprog(param) for param in ops]

        os.chdir(cwd)

def zipmapdata():
    '''
    cd merged

    ..\..\..\..\th0_tmc -checktmc
    ..\..\..\..\mapzip thin\mapdata1b.raw mapdata1.raz
    ..\..\..\..\mapzip thin\mapdata2b.raw mapdata2.raz
    del /Q thin\*
    rmdir thin
    '''

    cwd = os.getcwd()
    os.chdir(os.path.join(path_mgr.get_dici_dir(), 'merged'))

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'th0_tmc'), '-checktmc'],
        [os.path.join(path_mgr.get_tools_path(), 'mapzip'),
         os.path.join('thin', 'mapdata1b.raw'), 'mapdata1.raz'],
        [os.path.join(path_mgr.get_tools_path(), 'mapzip'),
         os.path.join('thin', 'mapdata2b.raw'), 'mapdata2.raz'],)

    #if path_mgr.get_cfg().for_hybrid:
    #   ops.append([os.path.join(path_mgr.get_tools_path(), 'mapzip'),
    #   'poi.raw', r'maps\poi.biz'])

    [runprog(param) for param in ops]

    shutil.rmtree('thin')
    os.chdir(cwd)

def ziplinkinfo():
    '''
    ..\..\..\..\genname
    ..\..\..\..\mapzip lfoidx.raw lfoidx.raz
    ..\..\..\..\mapzip linkinfo.raw linkinfo.raz
    ..\..\..\..\cutall -checktmc
    '''

    cwd = os.getcwd()
    os.chdir(os.path.join(path_mgr.get_dici_dir(), 'merged'))

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'genname')],
        [os.path.join(path_mgr.get_tools_path(), 'mapzip'), 'lfoidx.raw', 'lfoidx.raz'],
        [os.path.join(path_mgr.get_tools_path(), 'mapzip'), 'linkinfo.raw', 'linkinfo.raz'],
        [os.path.join(path_mgr.get_tools_path(), 'cutall'), '-checktmc'],
        )

    [runprog(param) for param in ops]

    os.chdir(cwd)

def remove_files(root, ext = '*.*'):
    for file in glob.glob(os.path.join(root, ext)):
        os.remove(file)

def cutpostprocess():
    '''
    cd maps
    ..\..\..\..\..\CutPostProcess
    del /Q *.tmp
    cd ..\..\..\..\..
    '''

    cwd = os.getcwd()
    src_path = os.path.join(path_mgr.get_dici_dir(), 'merged', 'maps');
    os.chdir(src_path)

    args = [os.path.join(path_mgr.get_tools_path(), 'CutPostProcess.exe')]
    runprog(args)

    #need copt lfopos.new and namefpos.new
    if path_mgr.get_cfg().for_hybrid:
      dst_path = os.path.join(path_mgr.get_dici_dir(), 'merged', 'shrunk')
      move_file(src_path, 'lfopos.new', dst_path)
      move_file(src_path, 'namefpos.new', dst_path)

    os.chdir(cwd)
#===================================================
#phase2 steps
#===================================================
def prepare_poly():
    '''prepare polygon processing'''
    if path_mgr.get_cfg().do_outer_ploygon:
        for key in ['ow', 'nf']:
                dst = os.path.join(path_mgr.get_dici_dir(), key)
                make_dir(dst, True)
                cp_dir = None
                if key == 'ow':
                    cp_dir = path_mgr.get_cfg().ow_path;
                elif key == 'nf':
                    cp_dir = path_mgr.get_cfg().nf_path;
                else:
                    assert(False)
                if path_mgr.get_cfg().for_hybrid:
                    copy_file(cp_dir, 'polygons1.raw', dst)
                    copy_file(cp_dir, 'polygons2.raw', dst)
                    copy_file(cp_dir, 'polygons3.raw', dst)
                    #copy_file(cp_dir, 'buildings.raw', dst)
                    copy_file(cp_dir, 'pointfeats.raw', dst)
                else:
                    copy_file(cp_dir, 'polygons.raw', dst)
                    copy_file(cp_dir, 'polygons64.raw', dst)
                    copy_file(cp_dir, 'polygons128.raw', dst)
                    copy_file(cp_dir, 'polygons256.raw', dst)
                    copy_file(cp_dir, 'polygons1024.raw', dst)
                    copy_file(cp_dir, 'polygons4096.raw', dst)
                    copy_file(cp_dir, 'pointfeats.raw', dst)

def polyfgen():

    exec_name = 'polyfZgen.exe'
    cwd = os.getcwd()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)

            ops = ([os.path.join(path_mgr.get_tools_path(), exec_name), dst, '-pt', str(prodtype)],
                  [os.path.join(path_mgr.get_tools_path(), exec_name),'-b', dst],)
            if path_mgr.get_cfg().st == ST_TA:
                  ops[0].append('-ta')
            [runprog(param) for param in ops]

    os.chdir(cwd)

def polyfthin_hybrid():

    cwd = os.getcwd()
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)
            ops =([os.path.join(path_mgr.get_tools_path(), 'polyfthin'), '-eudata'],)
            [runprog(x) for x in ops]

    os.chdir(cwd)

def polyfthin_one(p1, p2, p3, full = False):

    cwd = os.getcwd()
    for keys, country, path in path_mgr.get_data_input_dirs().values():
        for key in keys:
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)
            ofname = 'polygons%s' % p1;
            if full:
                ops =([os.path.join(path_mgr.get_tools_path(), 'polyfthin'),'-eudata', '-f', ofname],)
            else:
                ops =([os.path.join(path_mgr.get_tools_path(), 'polyfthin'), '-thin', p1, p2, p3,'-eudata', '-f', ofname],)
            [runprog(x) for x in ops]

    os.chdir(cwd)

def polyfthin_nonhybrid():

    polyfthin_one('64', '16', '10')
    polyfthin_one('128','4','8')
    polyfthin_one('256','4','8')
    polyfthin_one('1024','4','6')
    polyfthin_one('4096','4','6')
    polyfthin_one('', '', '', True)

def stitchpolythin_one(rawpolyname, forpoly = True):

    os.chdir(path_mgr.get_dici_dir())

    (only_one, subDca) = is_only_one_subdca(True)
    full_name = '%s.raw' % rawpolyname

    if only_one and not path_mgr.get_cfg().do_outer_ploygon:
        #not call stitch.exe, copy data to merge directory
        src = os.path.join(path_mgr.get_dici_dir(), subDca)
        dst = os.path.join(path_mgr.get_dici_dir(), 'merged')
        copy_file(src, full_name, dst, full_name)

    else:
        cfg_name = 'Test.in'
        if forpoly:
            if path_mgr.get_cfg().do_outer_ploygon:
                cfg_name = 'TestOW.in'
                make_stitch_cfg(cfg_name, ['ow', 'nf'], False, True)
            else:
                make_stitch_cfg(cfg_name, [], False, True)
            args=[os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name, '.', '-fname', rawpolyname]
        else:
            make_stitch_cfg(cfg_name, [], False, True)
            mergeddir = os.path.join(path_mgr.get_dici_dir(), 'merged')
            args=[os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name, '.', '-labelbbox']
            
        runprog(args)
            
def stitchpoly_one(p1):

    cfg_name = 'Test.in'
    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            src = os.path.join(path_mgr.get_sif_dir(), key)
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)
            curf = 'polygons' + p1
            #copy_file(dst, curf, dst, 'polygons.raw')

    os.chdir(path_mgr.get_dici_dir())

    args=[os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name, '.', '-f', curf]
    runprog(args)

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    move_file(merged_dir, 'polygons.raw',merged_dir,'polygons%s.raw' % p1)

def stitchpolyons():

    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())

    cfg_name = 'Test.in'
    make_stitch_cfg(cfg_name, [], False, True)

    if path_mgr.get_cfg().for_hybrid:
        stitchpoly_one('1')
        stitchpoly_one('2')
        stitchpoly_one('3')
    else:
        stitchpolythin_one('polygons64')
        stitchpolythin_one('polygons128')
        stitchpolythin_one('polygons256')
        stitchpolythin_one('polygons1024')
        stitchpolythin_one('polygons4096')
        stitchpolythin_one('polygons')
        stitchpolythin_one('labelbboxs', False)


def stitchbuildings():

    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())
    cfg_name = 'Test.in'
    make_stitch_cfg(cfg_name, [], False, True)
    os.chdir(path_mgr.get_dici_dir())

    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)
            ops = ([os.path.join(path_mgr.get_tools_path(), 'polyfthin'), '-eudata', '-b'],)
            [runprog(param) for param in ops]

    os.chdir(path_mgr.get_dici_dir())

    (only_one, subDca) = is_only_one_subdca(True)

    if only_one:
        #not call stitch.exe, copy data to merge directory
        src = os.path.join(path_mgr.get_dici_dir(), subDca)
        dst = os.path.join(path_mgr.get_dici_dir(), 'merged')
        copy_file(src, 'buildings.raw', dst)

    else:
        if path_mgr.get_cfg().for_hybrid:
            ops =([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name, '.','-f', 'buildings'],)
        else:
            ops = ([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name, '.','-buildings'],)

        [runprog(param) for param in ops]

    os.chdir(cwd)

def thin_shrink_poly(bname, id_in, id_out, merged_dir):
    """Run thinpoly, mapzipcmpshrink, for polygon files, using ID values."""

    maps_dir = os.path.join(merged_dir, 'maps')
    raw_filename = '%s%s.raw' % (bname, id_in)
    assert os.path.exists(raw_filename), 'File not found: %s' % raw_filename

    args = (os.path.join(path_mgr.get_tools_path(), 'thinpoly'), raw_filename, '-ta')

    runprog(args)

    thn_filename = raw_filename + '.thnshp'
    assert os.path.exists(thn_filename), 'File not found: %s' % thn_filename
    args = (os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'), thn_filename,
        os.path.join(maps_dir, ('%s.biz.%s' % (bname, id_out))))
    runprog(args)

    src_path = os.path.join(merged_dir, thn_filename)
    remove_file(src_path)

    remove_file('polynameslist.dat')
    rename_file(merged_dir, 'polynameslistOut.dat', 'polynameslist.dat')

def shrinkpolygons():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_maps_dir = os.path.join(merged_dir, 'shrunk', 'maps')

    os.chdir(merged_dir)
    for fname in ('polynameslist.dat', 'polynamelistOut.dat','polynamesIn.dat','labelbboxs.idx'):
        path = os.path.join(merged_dir, fname)
        remove_file(path)

    if path_mgr.get_cfg().for_hybrid:
        thin_shrink_poly('polygons', '1', '1', merged_dir)
        thin_shrink_poly('polygons', '2', '2',merged_dir)
        thin_shrink_poly('polygons', '3', '3',merged_dir)
        thin_shrink_poly('buildings', '', '', merged_dir)
    else:
        thin_shrink_poly('polygons', '', '',merged_dir)
        thin_shrink_poly('polygons', '4096', '1', merged_dir)
        thin_shrink_poly('polygons', '1024', '2',merged_dir)
        thin_shrink_poly('polygons', '256', '3', merged_dir)
        thin_shrink_poly('polygons', '128', '4', merged_dir)
        thin_shrink_poly('polygons', '64', '5', merged_dir)
        thin_shrink_poly('buildings', '', '', merged_dir)

    #move polygons series
    max_poly_index = 6
    if path_mgr.get_cfg().for_hybrid:
        max_poly_index = 4

    else:
        copy_file(merged_maps_dir, 'polygons.biz', shrunk_maps_dir)
        move_file(merged_dir, 'polynames.bin', shrunk_maps_dir)

    copy_file(merged_maps_dir, 'buildings.biz', shrunk_maps_dir)

    #need copy polygons.biz.x to shrunk/maps
    for x in range(1, max_poly_index):
        filename = 'polygons.biz.%d' % x
        copy_file(merged_maps_dir, filename, shrunk_maps_dir)

    os.chdir(cwd)

def dedupingpointfeats():
    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())
    #copy merged/pointfeats.raw to mergedbak dir
    merge_dir = os.path.join(path_mgr.get_dici_dir(), 'merged')
    newow_dir = os.path.join(path_mgr.get_dici_dir(), 'newow')
    mergebak_dir = os.path.join(path_mgr.get_dici_dir(), 'mergedbak')

    make_dir(newow_dir)
    make_dir(mergebak_dir)
    copy_file(merge_dir, 'pointfeats.raw', mergebak_dir)

    #run owdeduping
    args = ([os.path.join(path_mgr.get_tools_path(), 'owdeduping.exe'),
            '-ow', os.path.join(path_mgr.get_dici_dir(), 'ow', 'pointfeats.raw'),
            '-ref', os.path.join(merge_dir, 'pointfeats.raw'),
            '-t', '2', '-o', os.path.join(newow_dir, 'pointfeats.raw')])
    runprog(args)


def stitchpointfeats():
    cwd = os.getcwd()
    os.chdir(path_mgr.get_dici_dir())
    cfg_name = 'Test.in'
    make_stitch_cfg(cfg_name, [], False, True)

    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            dst = os.path.join(path_mgr.get_dici_dir(), key)
            os.chdir(dst)
            args = ([os.path.join(path_mgr.get_tools_path(), 'polyfthin'), '-points','-thinmult','16'])

            runprog(args)

    os.chdir(path_mgr.get_dici_dir())

    (only_one, subDca) = is_only_one_subdca(True)

    if only_one:
        #not call stitch.exe, copy data to merge directory
        src = os.path.join(path_mgr.get_dici_dir(), subDca)
        dst = os.path.join(path_mgr.get_dici_dir(), 'merged')
        copy_file(src, 'pointfeats.raw', dst)

    else:
        #stitch normal with keys
        if path_mgr.get_cfg().for_hybrid:
            args = ([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name,'.', '-f', 'pointfeats'])
        else:
            args = ([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name,'.','-points'])

        runprog(args)

    if path_mgr.get_cfg().do_outer_ploygon:

        #need dedupig pointfeat first
        dedupingpointfeats()

        #then stitch to new pointfeat which is deduped
        cfg_name = 'TestOW.in'
        make_stitch_cfg(cfg_name, ['newow', 'mergedbak'], True, True)

        if path_mgr.get_cfg().for_hybrid:
            args = ([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name,'.', '-f', 'pointfeats'])
        else:
            args = ([os.path.join(path_mgr.get_tools_path(), 'stitchpoly'), cfg_name,'.','-points'])

        runprog(args)

    os.chdir(cwd)

def shrinkpointfeats():

    cwd = os.getcwd()
    merged_dir = os.path.join(path_mgr.get_dici_dir(), 'merged')
    maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_maps_dir = os.path.join(merged_dir, 'shrunk', 'maps')

    os.chdir(merged_dir)
    for fname in ('pointnameslist.dat', 'pointnamelistOut.dat',
        'pointnamesIn.dat'):
        path = os.path.join(merged_dir, fname)
        remove_file(path)

    raw_filename = 'pointfeats.raw'
    assert os.path.exists(raw_filename), 'File not found: %s' % raw_filename
    args = (os.path.join(path_mgr.get_tools_path(), 'thinpoly'), raw_filename, '-points')
    runprog(args)

    thn_filename = raw_filename + '.thnshp'
    biz_filename = 'pointfeats.biz'
    assert os.path.exists(thn_filename), 'File not found: %s' % thn_filename
    args = (os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'), thn_filename,
        os.path.join(maps_dir, biz_filename))
    runprog(args)

    path = os.path.join(merged_dir, thn_filename)
    remove_file(path)


    shrunk_maps_dir = os.path.join(merged_dir, 'shrunk', 'maps')
    copy_file(maps_dir, 'pointfeats.biz', shrunk_maps_dir)

    if not path_mgr.get_cfg().for_hybrid:
        os.rename('pointnameslistOut.dat', 'pointnameslist.dat')
        move_file(merged_dir, 'pointnames.bin', shrunk_maps_dir)

    os.chdir(cwd)

#===================================================
#phase3 steps
#===================================================
def prepare_shrink():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    newcase_dir = os.path.join(shrunk_dir, 'newcase')
    make_dir(newcase_dir)

    oldcase_dir = os.path.join(shrunk_dir, 'oldcase')
    make_dir(oldcase_dir)


    #copy *.ini and *.txt files
    for fname in ('aztypesUS.txt', 'extraneousUS.txt',
                  'ProdMap.ini', 'ProdDefault.ini', 'ProdRouting.ini',
                  'prefixesUS.txt', 'skipwords.txt', 'sttypesUS.txt',
                  'Unicode_allkeys.txt', 'PhGenProd.ini', 'admintypes.xml',
                  'MapInfo.ini'):
        copy_file(path_mgr.get_tools_path(), fname, shrunk_maps_dir)

    copy_file(path_mgr.get_tools_path(), 'WellKnownWords.txt', merged_dir)
    copy_file(path_mgr.get_tools_path(), 'WellKnownPointnames.txt', merged_dir)
    
    #copy linkids.manf to shrink/maps folder
    copy_file(path_mgr.get_dici_dir(), 'linkids.manf', shrunk_maps_dir)
    
    #need copy files
    for fname in os.listdir(merged_maps_dir):
        if (fname.startswith('az.') or fname.startswith('ls') or
            fname.startswith('n') or fname.startswith('str') or
            fname.startswith('stt') or fname.startswith('polynames')
            or fname.startswith('pointname')):
                copy_file(merged_maps_dir, fname, shrunk_maps_dir)

    os.chdir(cwd)

def post_name_proc():

    #processing names related files
    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    newcase_dir = os.path.join(shrunk_dir, 'newcase')
    make_dir(newcase_dir)

    oldcase_dir = os.path.join(shrunk_dir, 'oldcase')
    make_dir(oldcase_dir)

    #case changer
    empty_dir(newcase_dir)

    os.chdir(shrunk_dir)
    ops = [(os.path.join(path_mgr.get_tools_path(), 'CaseChanger'), 'maps', 'newcase'),]

    if not path_mgr.get_cfg().for_hybrid:
      ops.append((os.path.join(path_mgr.get_tools_path(), 'CaseChanger'), '-points', 'maps', 'newcase'))

    [runprog(x) for x in ops]

    #move files
    def shuffle_file(filename):
        move_file(shrunk_maps_dir, filename, oldcase_dir)
        move_file(newcase_dir, filename, shrunk_maps_dir)

    shuffle_file('az.bin')
    shuffle_file('lsrs.bin')
    shuffle_file('names.bin')

    if not path_mgr.get_cfg().for_hybrid:
        shuffle_file('polynames.bin')
        shuffle_file('pointnames.bin')
    else:
        #copy fake files:polygones.biz and polyname.bin
        copy_file(shrunk_maps_dir, 'polygons.biz.1', shrunk_maps_dir, 'polygons.biz')
        copy_file(shrunk_maps_dir, 'names.bin', shrunk_maps_dir, 'polynames.bin')
        copy_file(shrunk_maps_dir, 'names.bin', shrunk_maps_dir, 'pointnames.bin')

    os.chdir(shrunk_maps_dir)

    #SpellChecker.exe
    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'SpellChecker.exe'),
         '-i:'+shrunk_maps_dir,
         '-o:'+shrunk_maps_dir,
         ],
    )
    [runprog(x) for x in ops]


def shrink_mapdata():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    make_dir(shrunk_dir)

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    make_dir(shrunk_maps_dir)

    os.chdir(shrunk_dir)

    # Specifically: shrinkmap2TmcZipTzDtmDiciLfoNode requires a relative path
    r_merged_dir = os.path.join('..')
    r_merged_maps_dir = os.path.join(r_merged_dir, 'maps')
    r_shrunk_dir = os.path.join('.')
    r_shrunk_maps_dir = os.path.join(r_shrunk_dir, 'maps')

    copy_file(path_mgr.get_tools_path(), 'TMCbyTable.csv', shrunk_dir)
    copy_file(merged_maps_dir, 'az.bin', shrunk_dir)

    if path_mgr.get_cfg().for_hybrid:
      ops = ([os.path.join(path_mgr.get_tools_path(), 'shrinkLFOspatial')],)
    else:
        ops = (
               [os.path.join(path_mgr.get_tools_path(), 'shrinkLFOzipcodeRteGen')],
               [os.path.join(path_mgr.get_tools_path(), 'shrinkLFOzipcodeRteApply')])

    [runprog(x) for x in ops]

    move_file(shrunk_dir, 'linkinfo.new', shrunk_maps_dir, 'linkinfo.bin')
    move_file(shrunk_dir, 'HuffCodeLFO.dat', shrunk_maps_dir)


    #handle with poi here
    if path_mgr.get_cfg().for_hybrid:
          copy_file(merged_dir, 'poi.raw', merged_dir, 'poi.raw.bk');
          ops = [os.path.join(path_mgr.get_tools_path(), 'poipvidreplacer'), '-i',
                merged_dir, '-mf', shrunk_dir]
          runprog(ops)

          rename_file(merged_dir, 'poi.raw', 'poi.bin');
          rename_file(merged_dir, 'poi.raw.bk', 'poi.raw');

          ops = [os.path.join(path_mgr.get_tools_path(), 'mapzip'), os.path.join(merged_dir, 'poi.bin'),
                os.path.join(shrunk_maps_dir, 'poi.biz')]
          runprog(ops)


    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
         os.path.join(shrunk_dir, 'lfonamepos.bin'),
         os.path.join(shrunk_maps_dir, 'lfonamepos.biz')],
    )
    [runprog(x) for x in ops]

    path = os.path.join(shrunk_dir, 'lfonodefileACC.dat')
    remove_file(path)

    path = os.path.join(shrunk_dir, 'links.ids')
    remove_file(path)

    SpatialFlag = ''
    if path_mgr.get_cfg().for_hybrid:
      SpatialFlag = '-SpatialLfo'

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'shrinkmap2TmcZipTzDtmDiciLfoNode'), SpatialFlag,
         os.path.join(r_merged_maps_dir, 'mapdata2.biz')],
        [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrinksuperbin'),
         os.path.join(shrunk_dir, 'mapdata2.biz.int'),
         os.path.join(shrunk_maps_dir, 'mapdata2.biz')],
    )
    [runprog(x) for x in ops]

    path = os.path.join(shrunk_dir, 'mapdata2.biz.int')
    remove_file(path)

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'shrinkmap1TmcZipTzDtmDiciLfoNode'), SpatialFlag,
         os.path.join(r_merged_maps_dir, 'mapdata1.biz')],
        [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
         os.path.join(shrunk_dir, 'mapdata1.biz.int'),
         os.path.join(shrunk_maps_dir, 'mapdata1.biz')],
    )
    [runprog(x) for x in ops]

    path = os.path.join(shrunk_dir, 'mapdata1.biz.int')
    remove_file(path)

    # Sort segmentID with PVID by using links.idx.
    args = (os.path.join(path_mgr.get_tools_path(), 'SortSegmentIDwithPVID'), shrunk_dir,
            shrunk_maps_dir, '-bin')
    runprog(args)

    # New utility that sorts and merges -- might need relative directories.
    lfonodeacc_file = os.path.join(shrunk_dir, 'lfonodefileACC.dat')
    lfonodedat_file = os.path.join(shrunk_maps_dir, 'lfonodefile.dat')
    args = (os.path.join(path_mgr.get_tools_path(), 'SortLfoNodeRecFile'), lfonodeacc_file,
            lfonodedat_file, '-compact')
    runprog(args)

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'shrinkmap1TmcZipTzDtmDici'), SpatialFlag,
         os.path.join(r_merged_maps_dir, 'mapdatat.biz')],
        [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
         os.path.join(shrunk_dir, 'mapdatat.biz.int'),
         os.path.join(shrunk_maps_dir, 'mapdatat.biz')],
    )
    [runprog(x) for x in ops]

    path = os.path.join(shrunk_dir, 'mapdatat.biz.int')
    remove_file(path)


    argv = [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
         os.path.join(merged_maps_dir, 'stnl.bin'),
         os.path.join(shrunk_maps_dir, 'stnl.biz')]

    runprog(argv)

    if path_mgr.get_cfg().for_hybrid:
      argv = [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
           os.path.join(shrunk_maps_dir, 'linkinfo.unz'),
           os.path.join(shrunk_maps_dir, 'linkinfo.biz')]

      runprog(argv)

      argv = [os.path.join(path_mgr.get_tools_path(), 'mapzipcmpshrink'),
           os.path.join(shrunk_dir, 'streets.bin'),
           os.path.join(shrunk_maps_dir, 'streets.biz')]

      runprog(argv)


    #need copy files
    for fname in os.listdir(merged_maps_dir):
      if fname.startswith('stt'):
        copy_file(merged_maps_dir, fname, shrunk_maps_dir)


    if not path_mgr.get_cfg().for_hybrid:
        ops = (
               [os.path.join(path_mgr.get_tools_path(), 'mapziplfoidxbiglfo'),
                os.path.join(merged_maps_dir, 'lfoidx.bin'),
                os.path.join(shrunk_maps_dir, 'lfoidx.bin')],
                )
        [runprog(x) for x in ops]

    copy_file(shrunk_dir, 'TMCtables.dat', shrunk_maps_dir, 'auxdata.dat')

    for fname in ('zip.bin', 'tz.txt', 'buildings.biz','pointfeats.biz', 'pointnames.bin','polynames.bin'):
        copy_file(merged_maps_dir, fname, shrunk_maps_dir)

    os.chdir(cwd)

def linkstt_gen():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    make_dir(shrunk_dir)

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    make_dir(shrunk_maps_dir)

    os.chdir(shrunk_dir)

    #REM TomTom Original ID with Segment ID,
    #..\..\..\..\..\TomTomOriginalIDwithSegmentID.exe -l .\maps\links.bin -t ..\linksTT.bin -o .\maps\links64.bin
    argv = [os.path.join(path_mgr.get_tools_path(), 'TomTomOriginalIDwithSegmentID'),
            '-l', os.path.join(shrunk_maps_dir, 'links.bin'),
            '-t', os.path.join(merged_dir, 'linksTT.bin'),
            '-o', os.path.join(shrunk_maps_dir, 'links64.bin')]

    runprog(argv)

    os.chdir(cwd)
    
def post_pointaddr_proc():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    make_dir(shrunk_maps_dir)

    os.chdir(shrunk_maps_dir)
    argv = [os.path.join(path_mgr.get_tools_path(), 'PointAddrTool'), '-TT', 
            merged_dir, shrunk_maps_dir, path_mgr.get_region()]
    runprog(argv)

    mapinfo_modify(True)
    argv = [os.path.join(path_mgr.get_tools_path(), 'PointAddrPvid2Lfofpos'),'-TT', '.\ProdMap.ini']
    runprog(argv)
    
		#restore the mapinfo.ini
    mapinfo_modify(False)
    #reomve unwanted file - pvid2papos.idx 
    remove_file(os.path.join(shrunk_maps_dir, 'pvid2papos.idx'))

def post_PointAddrTool_proc():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    make_dir(shrunk_maps_dir)

    os.chdir(shrunk_maps_dir)
    argv = [os.path.join(path_mgr.get_tools_path(), 'PointAddrTool'), '-TT', 
            merged_dir, path_mgr.get_existing_map_path_dir(), path_mgr.get_region()]
    runprog(argv)

def post_PointAddrPvid2Lfofpos_proc():
    cwd = os.getcwd()
    os.chdir(path_mgr.get_existing_map_path_dir())
    mapinfo_modify(True)
    argv = [os.path.join(path_mgr.get_tools_path(), 'PointAddrPvid2Lfofpos'),'-TT', '.\ProdMap.ini']
    runprog(argv)
    
	#restore the mapinfo.ini
    mapinfo_modify(False)
    remove_file(os.path.join(path_mgr.get_tools_path(), 'pvid2papos.idx'))

def sigmod():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    make_dir(shrunk_dir)


    os.chdir(shrunk_dir)


    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(path_mgr.get_tools_path(), 'MapInfo.ini'))

    app_path = os.path.join(path_mgr.get_tools_path(), 'sigmod')
    signatures_map = [
                ('mapdata1.biz', config.get('EngineConfig', 'MapdataSig')),
                ('mapdata2.biz', config.get('EngineConfig', 'MapdataSig')),
                ('mapdatat.biz', config.get('EngineConfig', 'MapdataSig')),
                ('pointfeats.biz', config.get('EngineConfig', 'PolyBizSig')),
                ('polygons.biz', config.get('EngineConfig', 'PolyBizSig')),
                ('polygons.biz.1', config.get('EngineConfig', 'PolyBizSig')),
                ('polygons.biz.2', config.get('EngineConfig', 'PolyBizSig')),
                ('polygons.biz.3', config.get('EngineConfig', 'PolyBizSig')),
                ('polynames.bin', config.get('EngineConfig', 'PolyNamesSig')),
                ('pointnames.bin', config.get('EngineConfig', 'PointNamesSig')),
                ]

    if path_mgr.get_cfg().for_hybrid:
        #copy fake files:polygones.biz and polyname.bin
        copy_file(shrunk_maps_dir, 'polygons.biz.1', shrunk_maps_dir, 'polygons.biz')
        copy_file(shrunk_maps_dir, 'names.bin', shrunk_maps_dir, 'polynames.bin')
        copy_file(shrunk_maps_dir, 'names.bin', shrunk_maps_dir, 'pointnames.bin')

        signatures_map.append(('linkinfo.unz', config.get('EngineConfig', 'LinkInfoSig')))
        signatures_map.append(('linkinfo.biz', config.get('EngineConfig', 'LinkInfoSig')))
        signatures_map.append(('poi.biz', config.get('EngineConfig', 'PoiBizSig')))
    else:
        signatures_map.append(('lfoidx.bin', config.get('EngineConfig', 'LfoIdxSig')))
        signatures_map.append(('linkinfo.bin', config.get('EngineConfig', 'LinkInfoSig')))
        signatures_map.append(('polygons.biz.4', config.get('EngineConfig', 'PolyBizSig')))
        signatures_map.append(('polygons.biz.5', config.get('EngineConfig', 'PolyBizSig')))

    for fname, sig in signatures_map:
        file_path = os.path.join(shrunk_maps_dir, fname)
        runprog([app_path, file_path, sig])

    os.chdir(cwd)

def mapinfo_modify(in_proc):
  '''modify MapInfo.ini for different usage'''

  merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
  shrunk_maps_dir = os.path.join(merged_dir, 'shrunk', 'maps')

  info_ini = 'MapInfo.ini'
  prod_ini = 'MapInfoProd.ini'
  if path_mgr.get_region() == 'EU':
    info_ini = 'MapInfoEU.ini'
    prod_ini = 'MapInfoEUProd.ini'

  if in_proc:
    copy_file(path_mgr.get_tools_path(), prod_ini, shrunk_maps_dir, 'MapInfo.ini')
  else:
    copy_file(path_mgr.get_tools_path(), info_ini, shrunk_maps_dir, 'MapInfo.ini')


def multiword_proc():

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    os.chdir(shrunk_maps_dir)

    #MultiWordTool.exe processing
    mapinfo_modify(True)
    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'MultiWordTool.exe'), '-V', '-D', '-I:mwnames',
         '.\ProdMap.ini'],
    )
    [runprog(x) for x in ops]

    mapinfo_modify(False)
    rename_file(shrunk_maps_dir, 'mwnames_01.ddx', 'mwnames.ddx')

def ddxbuild():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    mapinfo_modify(True)

    if path_mgr.get_cfg().for_hybrid:
        os.chdir(shrunk_dir)
        ops = [os.path.join(path_mgr.get_tools_path(), 'lfoFposMapBuilder.exe')]
        runprog(ops)

        os.chdir(shrunk_maps_dir)

        for fname in ('azst', 'zipst', 'statest', 'ststate'):
            ops = [os.path.join(path_mgr.get_tools_path(), 'ddxBuilder.exe'), '-I', fname]
            runprog(ops)

    else:
        os.chdir(shrunk_maps_dir)

        copy_file(path_mgr.get_tools_path(), 'geocountrywhitelist.txt', shrunk_maps_dir)

        for fname in ('azst', 'zipst', 'statest', 'ststate'):
            ops = (
              [os.path.join(path_mgr.get_tools_path(), 'LfoTool.exe'), '-V', '-D', '-mw',
               '-I:%s' % fname, '-M', '.\ProdMap.ini'],)
            [runprog(x) for x in ops]

            rename_file(shrunk_maps_dir, '%s_01.ddx' % fname, '%s.ddx' % fname)

        for fname in ('azst', 'zipst'):
            ops = (
              [os.path.join(path_mgr.get_tools_path(), 'LfoTool.exe'), '-V', '-D',
               '-N:%s' % fname, '.\ProdMap.ini'],)
            [runprog(x) for x in ops]

            rename_file(shrunk_maps_dir, '%s_01.nod' % fname, '%s.nod' % fname)

        #remove the geocountrywhitelist.txt
        remove_file(os.path.join(shrunk_maps_dir, 'geocountrywhitelist.txt'))

    mapinfo_modify(False)

def repair_laneinfo():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    os.chdir(shrunk_dir)
    ops = [os.path.join(path_mgr.get_tools_path(), 'LaneSpatial.exe'),
            '-mi', merged_maps_dir,
            '-ri', merged_dir,
            '-ni', shrunk_dir,
            '-o', shrunk_maps_dir]
    runprog(ops)

    os.chdir(cwd)

def find_TA_voice_files(root, key):
    voice_files = []
    for path, dirs, files in os.walk(root):
        for file in files:
            if file.endswith('_nefa.txt') or file.endswith('_ne.txt') or file.endswith('_pt.txt'):
                voice_files.append(file)
    return voice_files

def find_NT_voice_files(root, key):
    voice_files = []
    for path, dirs, files in os.walk(root):
        for file in files:
            if file.startswith(key) and (file.endswith('vif.txt') or file.endswith('vaf.txt')):
                voice_files.append(file)
    return voice_files

def find_voice_files(root, key):

    if path_mgr.get_cfg().st == ST_NT:
        return find_NT_voice_files(root, key)
    elif path_mgr.get_cfg().st == ST_TA:
        return find_TA_voice_files(root, key)

def phgen():
    #need copy vif.txt and vtf.txt first
    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    voice_dir = os.path.join(shrunk_dir, 'Voice')
    make_dir(voice_dir)

    os.chdir(shrunk_dir)

    for keys, country, prodtype in path_mgr.get_data_input_dirs().values():
        for key in keys:
            source_dir = os.path.join(path_mgr.get_sif_dir(), 'shpd', country, key)
            for file in find_voice_files(source_dir, key):
                copy_file(source_dir, file, voice_dir)

    os.chdir(shrunk_maps_dir)


    # Shuffle MapInfo.ini and MapInfoProd.ini.
    mapinfo_modify(True)

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'PhGen.exe'),
         os.path.join(shrunk_maps_dir, 'PhGenProd.ini')],
    )
    [runprog(x) for x in ops]

    #restore the mapinfo.ini
    mapinfo_modify(False)

    os.chdir(cwd)

def post_process(args):

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    spatial_dir = os.path.join(shrunk_maps_dir, 'spatial')
    make_dir(spatial_dir)

    if os.getcwd() != shrunk_maps_dir:
      os.chdir(shrunk_maps_dir)

    runprog(args)

def bofheader_gen():

    #run bofheader
    ops = [os.path.join(path_mgr.get_tools_path(), 'bofheader.exe'), '-p', '.\spatial']
    post_process(ops)

def bbtool():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    os.chdir(shrunk_maps_dir)

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'BBTool.exe'),
         os.path.join(shrunk_maps_dir, 'ProdMap.ini'),
         shrunk_maps_dir],
    )

    ops = [os.path.join(path_mgr.get_tools_path(), 'BBTool.exe'), '.\\ProdMap.ini', '.\\']

    runprog(ops)

def ssbtool():

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    os.chdir(shrunk_maps_dir)

    ops = [os.path.join(path_mgr.get_tools_path(), 'ssbtool.exe'),
           os.path.join(shrunk_maps_dir, 'MapInfo.ini'), shrunk_maps_dir]

    runprog(ops)

def statsgen():
    '''collection statistics'''

    cwd = os.getcwd()

    merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')

    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

    os.chdir(shrunk_maps_dir)

    ops = (
        [os.path.join(path_mgr.get_tools_path(), 'StatsGen.exe'),shrunk_maps_dir,
        '-all', '-o'],
        )
    [runprog(x) for x in ops]

CORE_FILES = ['az.bin',
              'zip.bin',
              'dtm.bin',
              'lsr.bin',
              'lsrs.bin',
              'addrs.bin',
              'names.bin',
              'admins.bin',
              'sttypes.bin',
              'categoryDict.bin',
              'poi.bizx',
              'buildings.bizx',
              'linkinfo.bizx',
              'mapdata1.bizx',
              'mapdata2.bizx',
              'mapdatat.bizx',
              'mapdatatdisp.bizx',
              'pointfeats.bizx',
              'streets.bizx',
              'streets.boff',
              'poi.boff',
              'buildings.boff',
              'linkinfo.boff',
              'mapdata1.boff',
              'mapdata2.boff',
              'mapdatat.boff',
              'mapdatatdisp.boff',
              'pointfeats.boff',
              'linkinfo.biz.boff',
              'polygons.bizx.1',
              'polygons.boff.1',
              'polygons.bizx.2',
              'polygons.boff.2',
              'polygons.bizx.3',
              'polygons.boff.3',
              'MapInfo.ini',
              'admintypes.xml',
              'auxdata.dat',
              'tz.txt',
              'skipwords.txt',
              'aztypesUS.txt',
              'sttypesUS.txt',
              'prefixesUS.txt',
              'extraneousUS.txt',
              'poiskipwords.txt',
              'Unicode_allkeys.txt']

def move_files():
    """Move the certain files to specific path."""
    merged_dir = os.path.join(path_mgr.get_dici_dir(), 'merged')
    merged_maps_dir = os.path.join(merged_dir, 'maps')
    shrunk_dir = os.path.join(merged_dir, 'shrunk')
    shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')
    # Move all files from /shrunk/maps/spatial to /shrunk/maps
    spatial_dir = os.path.join(shrunk_maps_dir, 'spatial')
    for item in os.listdir(spatial_dir):
        file_path = os.path.join(spatial_dir, item)
        shutil.move(file_path, shrunk_maps_dir)
    shutil.rmtree(spatial_dir)

    # Move the unneeded files from /shrunk/maps to /shrunk
    for item in os.listdir(shrunk_maps_dir):
        if item not in CORE_FILES:
            shutil.move(item, shrunk_dir)


def copy_ncdb():
    """Copy the output to the network."""
    maps_dir = path_mgr.get_maps_dir()
    shrunk_maps_dir = os.path.join(maps_dir, 'dici', 'merged', 'shrunk', 'maps')
    network_dir = os.path.join(path_mgr.get_network_dir(), 'maps', 'dici',
                               'merged', 'shrunk', 'maps')

    print 'Copying files...'
    print '  FROM: %s' % shrunk_maps_dir
    print '  TO:   %s' % network_dir
    shutil.copytree(shrunk_maps_dir, network_dir)
    print 'Complete.'

def post_proc():
  '''package NCDB'''

  cwd = os.getcwd()

  merged_dir = os.path.join(path_mgr.get_dici_dir(),'merged')
  merged_maps_dir = os.path.join(merged_dir, 'maps')
  shrunk_dir = os.path.join(merged_dir, 'shrunk')
  shrunk_maps_dir = os.path.join(shrunk_dir, 'maps')

  os.chdir(shrunk_maps_dir)

  backup_dir = os.path.join(shrunk_dir, 'backup')
  make_dir(backup_dir, True)

  # Move the unneeded files from /shrunk/maps to /shrunk/backup
  if path_mgr.get_cfg().for_hybrid:
    for item in os.listdir(shrunk_maps_dir):
        if item not in CORE_FILES:
            shutil.move(item, backup_dir)

  #if need copy resource
  if path_mgr.get_cfg().postopt.resrcproc:
    resource_dir = path_mgr.get_cfg().postopt.resrcpath
    if os.path.exists(resource_dir):
      copytree(resource_dir+'\\.', shrunk_maps_dir)

  #copy ncdb to target directory
  ncdb_dir = path_mgr.get_cfg().postopt.outpath
  if path_mgr.get_cfg().postopt.flat:
    if os.path.exists(ncdb_dir):
      copytree(shrunk_maps_dir, ncdb_dir)
  else:
      #rename the network output path
      rename_directories([ncdb_dir])
      new_ncdb_dir = os.path.join(ncdb_dir, 'maps', 'dici', 'merged', 'shrunk', 'maps')

      print 'Copying files...'
      print '  FROM: %s' % shrunk_maps_dir
      print '  TO:   %s' % new_ncdb_dir
      shutil.copytree(shrunk_maps_dir, new_ncdb_dir)
      print 'Complete.'

  #if need 7zip
  if path_mgr.get_cfg().postopt.pktproc:
    zip_name = os.path.join(ncdb_dir, 'map.7z')
    ops = [os.path.join(path_mgr.get_tools_path(), '7z.exe'), 'a', zip_name, '-r']
    runprog(ops)


  #restore cwd
  os.chdir(cwd)

#===================================================
#main process
#===================================================
class Counter:
    '''class counter for add one operation'''
    def __init__(self):
        self.seed = 0

    def auto_inc(self):
        tmp = self.seed
        self.seed += 1
        return tmp

    def get(self):
        return self.seed

    def reset(self):
        self.seed = 0

counter = Counter()

PROCESS_MAP = {}
def make_processing_map(options):
    '''generate processing mapping'''
    #global PROCESS_MAP
    #global counter
    counter.reset()
    PROCESS_MAP.clear()

    #phase1: sifsplit and sif2raw...
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase1 from this step'
    PROCESS_MAP[counter.auto_inc()] = make_output_dir

    if path_mgr.get_cfg().st == ST_NT:
        PROCESS_MAP[counter.auto_inc()] = sifsplit
        PROCESS_MAP[counter.auto_inc()] = sif2raw
        PROCESS_MAP[counter.auto_inc()] = sif2polygon
        PROCESS_MAP[counter.auto_inc()] = sif2buildings
        PROCESS_MAP[counter.auto_inc()] = sif2poi

        if path_mgr.get_cfg().do_lane_guidance:
            PROCESS_MAP[counter.auto_inc()] = sif2rawlaneinfo

        if path_mgr.get_cfg().do_dici:
            PROCESS_MAP[counter.auto_inc()] = proc_dici

    elif path_mgr.get_cfg().st == ST_TA:
        PROCESS_MAP[counter.auto_inc()] = tasplit
        PROCESS_MAP[counter.auto_inc()] = ta2raw
        PROCESS_MAP[counter.auto_inc()] = ta2polygon
        #PROCESS_MAP[counter.auto_inc()] = ta2poi
    
    if path_mgr.get_cfg().do_pointaddr:
        PROCESS_MAP[counter.auto_inc()] = ta2raw_pointaddr

    PROCESS_MAP[counter.auto_inc()] = stitch
    PROCESS_MAP[counter.auto_inc()] = zipmapdata
    PROCESS_MAP[counter.auto_inc()] = ziplinkinfo
    PROCESS_MAP[counter.auto_inc()] = cutpostprocess

    #phase2:thin and stitch polygons and buildings
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase2 from this step'
    if path_mgr.get_cfg().do_outer_ploygon:
        PROCESS_MAP[counter.auto_inc()] = prepare_poly

    PROCESS_MAP[counter.auto_inc()] = polyfgen

    if path_mgr.get_cfg().for_hybrid:
        PROCESS_MAP[counter.auto_inc()] = polyfthin_hybrid
    else:
        PROCESS_MAP[counter.auto_inc()] = polyfthin_nonhybrid

    PROCESS_MAP[counter.auto_inc()] = stitchpolyons
    PROCESS_MAP[counter.auto_inc()] = stitchbuildings
    PROCESS_MAP[counter.auto_inc()] = shrinkpolygons
    PROCESS_MAP[counter.auto_inc()] = stitchpointfeats
    PROCESS_MAP[counter.auto_inc()] = shrinkpointfeats

    #phase3:shrink map data
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase3 from this step'
    PROCESS_MAP[counter.auto_inc()] = prepare_shrink
    PROCESS_MAP[counter.auto_inc()] = post_name_proc
    PROCESS_MAP[counter.auto_inc()] = shrink_mapdata

    if path_mgr.get_cfg().st == ST_TA:
        PROCESS_MAP[counter.auto_inc()] = linkstt_gen

    PROCESS_MAP[counter.auto_inc()] = sigmod

    PROCESS_MAP[counter.auto_inc()] = multiword_proc
    PROCESS_MAP[counter.auto_inc()] = ddxbuild

    if path_mgr.get_cfg().do_lane_guidance:
        PROCESS_MAP[counter.auto_inc()] = repair_laneinfo
    
    if path_mgr.get_cfg().do_pointaddr: 
        PROCESS_MAP[counter.auto_inc()] = post_pointaddr_proc

    #phase4:post-process steps
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase4 from this step'
    PROCESS_MAP[counter.auto_inc()] = phgen

    if path_mgr.get_cfg().for_hybrid:
        PROCESS_MAP[counter.auto_inc()] = bofheader_gen
    else:
        PROCESS_MAP[counter.auto_inc()] = bbtool
        PROCESS_MAP[counter.auto_inc()] = ssbtool
        PROCESS_MAP[counter.auto_inc()] = statsgen

    if path_mgr.get_cfg().post_proc:
        PROCESS_MAP[counter.auto_inc()] = post_proc

def make_processing_pointaddr_map(options):
    '''generate processing mapping'''
    #global PROCESS_MAP
    #global counter
    counter.reset()
    PROCESS_MAP.clear()

    #phase1: sifsplit and sif2raw...
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase1 from this step'
    PROCESS_MAP[counter.auto_inc()] = make_output_dir
    PROCESS_MAP[counter.auto_inc()] = tasplit
    PROCESS_MAP[counter.auto_inc()] = ta2raw_pointaddr
    PROCESS_MAP[counter.auto_inc()] = stitch_pointaddr
    PROCESS_MAP[counter.auto_inc()] = post_PointAddrTool_proc
    PROCESS_MAP[counter.auto_inc()] = post_PointAddrPvid2Lfofpos_proc
HELP = ''

def make_processing_polygon_map(options):
    '''generate processing mapping'''
    #global PROCESS_MAP
    #global counter
    counter.reset()
    PROCESS_MAP.clear()

    #phase1: sifsplit and sif2raw...
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase1 from this step'
    PROCESS_MAP[counter.auto_inc()] = make_output_dir

    if path_mgr.get_cfg().st == ST_NT:
        PROCESS_MAP[counter.auto_inc()] = sif2polygon
        PROCESS_MAP[counter.auto_inc()] = sif2buildings
        PROCESS_MAP[counter.auto_inc()] = sif2poi
    elif path_mgr.get_cfg().st == ST_TA:
        PROCESS_MAP[counter.auto_inc()] = tasplit
        PROCESS_MAP[counter.auto_inc()] = ta2polygon

    #phase2:thin and stitch polygons and buildings
    PROCESS_MAP[counter.auto_inc()] = 'Start Processing Phase2 from this step'
    if path_mgr.get_cfg().do_outer_ploygon:
        PROCESS_MAP[counter.auto_inc()] = prepare_poly

    PROCESS_MAP[counter.auto_inc()] = polyfgen

    if path_mgr.get_cfg().for_hybrid:
        PROCESS_MAP[counter.auto_inc()] = polyfthin_hybrid
    else:
        PROCESS_MAP[counter.auto_inc()] = polyfthin_nonhybrid

    PROCESS_MAP[counter.auto_inc()] = stitchpolyons
    PROCESS_MAP[counter.auto_inc()] = stitchbuildings
    PROCESS_MAP[counter.auto_inc()] = shrinkpolygons
    PROCESS_MAP[counter.auto_inc()] = stitchpointfeats
    PROCESS_MAP[counter.auto_inc()] = shrinkpointfeats

    PROCESS_MAP[counter.auto_inc()] = sigmod


    if path_mgr.get_cfg().for_hybrid:
        PROCESS_MAP[counter.auto_inc()] = bofheader_gen

HELP = ''
def help():
    '''display help information'''

    print '\n========================================================'
    print 'This script is use for build NCDB(NIM Core Database)\n'
    print 'Process Steps:'
    for key, fun in PROCESS_MAP.iteritems():
        if isinstance(fun, FunctionType):
            print '\t%s\t%s' %(key, fun.__name__)
        elif isinstance(fun, str):
            print '\t%s\t%s' % (key, fun)
    print '========================================================\n'

    print HELP


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

    return options, args

def call_method(key, fun, log = None):
    if isinstance(fun, FunctionType):
        begin = 'Processing Step:%s: %s' %(key, fun.__name__)
        print begin
        if log:
            log.write(begin + '\n')
            log.flush()
        fun()
        end = 'Finished Step:%s: %s' %(key, fun.__name__)
        if log:
            log.write(end + '\n')
            log.flush()

    elif isinstance(fun, str):
        print fun


def build_ncdb(begin, end):
    '''build ncdb'''
    last_run_log = open('lastrun.log', 'w')
    for key, fun in PROCESS_MAP.iteritems():
        if key == begin and key <= end:
            call_method(key, fun, last_run_log)
            begin += 1
    last_run_log.close()

path_mgr = PathManager()
OPTION = None

def send_notice(cfg):
    subject = '[maps]NCDB MDC complete for ' + cfg.get_region()
    message = 'NCDB MDC process has completed for %(region)s ' \
        'on %(host)s.\n\n'
    message += 'COMMAND: %(cmd)s'
    kwargs = {'region': cfg.get_region(), 'host': hostname(),
              'cmd': ' '.join(sys.argv)}
    send_notification(subject, message, **kwargs)

def main(argv=None):

    #print sys._getframe().f_code.co_name
    (options, argv) = get_options(argv)
    global OPTION
    OPTION = options

    #loading configuration file
    path_mgr.load_cfg(options.config)

    if options.poly:
        make_processing_polygon_map(None)
    elif options.pointaddr:
        make_processing_pointaddr_map(None)
    else:
        make_processing_map(None)

    if options.help:
        help()
    else:
        #building ncdb
        begin = options.begin
        end = options.end
        if options.end < 0:
            end = len(PROCESS_MAP) - 1

        if end < begin:
            print 'invalid argument:end step must greater or equal to begin step'
        else:
            build_ncdb(begin, end)
            if options.notify:
                send_notice(path_mgr)


if __name__ == '__main__':
    main()
