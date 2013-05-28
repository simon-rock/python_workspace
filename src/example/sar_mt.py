#
# (C) Copyright 2010-2011 by TeleCommunication Systems, Inc.
#
# The information contained herein is confidential, proprietary
# to TeleCommunication Systems, Inc., and conside a trade secret as
# defined in section 499C of the penal code of the State of
# California. Use of this information by anyone other than
# authorized employees of TeleCommunication Systems is granted only
# under a written non-disclosure agreement, expressly
# prescribing the scope and manner of such use.
#
# sar.py: created 2010/07/09 by Mark Goddard.
#
#
# Requires:
# ElementTree (Present in Python 2.5 and later)
# Python Imaging Library (PIL)
#
# Requires Java Runtime Environment to be installed
# Requires batik-1.7 to be present in the expected folder

__version__ = '$Id: //depot/core/mobius/feature_120418_tomtom/Tools/Enhanced/python/signs_as_real/sar_mt.py#1 $'


from optparse import OptionParser
import glob
from lxml import etree as ET
#import xml.etree.ElementTree as ET
import os.path
import os
import sys
from PIL import Image
import Queue, threading
from threading import Thread
import time
from time import clock
import hashlib
import shutil
import copy
import string
import re

#sign panel border
STYLE_ATTRIB_WHITE = 'stroke:white;stroke-width:5'
STYLE_ATTRIB_RED = 'stroke:red;stroke-width:5'

g_landscape_width = 780.0
g_portrait_width = 460.0

g_default_width  = 1600.0
g_default_height = 600.0
g_addHalf = 400

#4 pixels for frame
g_max_height = 190.0

#min_height = 120
g_min_height = 170.0
g_min_height_p = 190.0

# Scale values (value by which to enlarge the image)
MAX_PORTRAIT_SCALE = 2.0
MAX_LANDSCAPE_SCALE = 2.0

#MAX_PORTRAIT_HEIGHT = 160.0
#MAX_LANDSCAPE_HEIGHT = 200.0
MAX_PORTRAIT_HEIGHT = 190.0
MAX_LANDSCAPE_HEIGHT = 190.0

IMAGE_WIDTH = 800 
IMAGE_HEIGHT = 600

global g_error_sar
g_error_sar = 0

class item:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.new_w = 0
        self.new_h = 0
		
# working thread
class Worker(Thread):
    worker_count = 0
    def __init__( self, workQueue, resultQueue, timeout = 0, **kwds):
        Thread.__init__( self, **kwds )
        self.id = Worker.worker_count
        Worker.worker_count += 1
        self.setDaemon( True )
        self.workQueue = workQueue
        self.resultQueue = resultQueue
        self.timeout = timeout
        self.start( )

    def run( self ):
        ''' the get-some-work, do-some-work main loop of worker threads '''
        while True:
            try:
                callable, args, kwds = self.workQueue.get(timeout=self.timeout)
                res = callable(*args, **kwds)
                #print "worker[%2d]: %s" % (self.id, str(res) )
                self.resultQueue.put( res )
            except Queue.Empty:
                break
            except :
                print 'worker[%2d]' % self.id, sys.exc_info()[:2]

class WorkerManager:
    def __init__( self, num_of_workers=10, timeout = 1):
        self.workQueue = Queue.Queue()
        self.resultQueue = Queue.Queue()
        self.workers = []
        self.timeout = timeout
        self._recruitThreads( num_of_workers )

    def _recruitThreads( self, num_of_workers ):
        for i in range( num_of_workers ):
            worker = Worker( self.workQueue, self.resultQueue, self.timeout )
            self.workers.append(worker)

    def wait_for_complete( self):
        # ...then, wait for each of them to terminate:
        while len(self.workers):
            worker = self.workers.pop()
            worker.join( )
            if worker.isAlive() and not self.workQueue.empty():
                self.workers.append( worker )
        print "All jobs are completed."

    def add_job( self, callable, *args, **kwds ):
        self.workQueue.put( (callable, args, kwds) )

    def get_result( self, *args, **kwds ):
       return self.resultQueue.get( *args, **kwds )

class NameObject:
    '''sar name object'''

    def __init__(self, filename):

        self.filename = filename
        self.name, self.ext = os.path.splitext(filename)
        self.path, self.fn = os.path.split(self.name)

    def get_png_name(self, sign_id, options):
        '''get png name'''
        name = '%s_%s.PNG' % (self.fn, sign_id)
        pngfile = os.path.join(options.outdir, name)
        return pngfile

    def get_ppng_name(self, sign_id, options):
        '''get png name'''
        name = '%s_%s_P.PNG' % (self.fn, sign_id)
        pngfile = os.path.join(options.outdir, name)
        return pngfile

    def get_svg_name(self, sign_id, options):
        svg_file = os.path.join(options.outdir, self.fn + "_" + sign_id + self.ext)
        return svg_file


def combine_tspan(e):
    t = ""
    for ts in e.findall('{http://www.w3.org/2000/svg}tspan'):
        t = t + ts.text
    return t

def find_text(e):
    for g in e.findall('{http://www.w3.org/2000/svg}g'):
        for t in find_text(g):
            yield t
    for t in e.findall('{http://www.w3.org/2000/svg}text'):
        ts = combine_tspan(t)
        if t.text:
            yield t.text
        elif ts:
            yield ts

def write_svg_with_pi(root, name):
    pi = ET.ProcessingInstruction(
        'xml-stylesheet',
        'type="text/css" href="%s"' % ('./customcolors.css')
        )
    root.getroot().addprevious(pi)
    root.write(name, pretty_print = True)


def process_sar_ennv_log_file(filename, error_log, options):

    if options.verbose:
        print "Processing: %s" % filename

    name, ext = os.path.splitext(filename)

    path, fn = os.path.split(name)
    try:
      doc = ET.parse(filename)
    except:
      info = 'Error: can not parse:%s\n' % filename
      error_log.write(info)
      raise

    #parse metadata map
    meta_map = {}
    for routes in doc.findall(r'{http://www.navteq.com/SaR3/1.0}routes'):
        pvid_src = routes.get('sourceLinkPVId', 'Invalid Source PVID')
        pvid_dst = ''
        for route in routes.findall(r'{http://www.navteq.com/SaR3/1.0}route'):
            pvid_dst = route.get('destinationLinkPVId', 'Invalid Destination PVID')
            ref_ids = set()
            #handle SVGObject
            for object in route.findall(r".//{http://www.navteq.com/SaR3/1.0}SVGObject"):
                #print 'ref_id', object.attrib['refId']
                ref_ids.add(object.attrib['refId'])

            meta_map[(pvid_src, pvid_dst)] = ref_ids
					
    (path, name) = os.path.split(filename)
    info = []
    info.append('#'+name)
    directions = 1
	
    #find right sign board
    for metak, metav in meta_map.items():
        vsign = []	
        for sign in doc.findall(r'{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}g'):
            for ids in sign.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                if ids.attrib['id'] in meta_map[(pvid_src, metak[1])]:
                    vsign.append(sign.attrib['id'])
                    break
		
        
        if not vsign:
            directions = directions + 1
            continue
			
        content = '%s:%s,%s' %('%s%s' % ('SIGN_L1R1_',directions), metak[0], metak[1])
        info.append(content)
        directions = directions + 1

    logfd = open(os.path.join(options.outdir, 'ennvsarinfo.log'), "a")
    logfd.write(('\n'.join(info) + '\n').encode("utf8"))
    logfd.flush()
    logfd.close()

def get_svg_bbx(name_obj, options):
    '''prepare sign board'''
    tmp_path = os.path.join(options.outdir, 'TMP')
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    name = '%s_TMP_0.PNG' % (name_obj.fn)
    pngfile = os.path.join(tmp_path, name)

    run_batik_rasterizer(name_obj.filename, pngfile, IMAGE_WIDTH, IMAGE_HEIGHT)
    im = Image.open(pngfile)
    (left, top, right, bottom) = im.getbbox()
    #print 'height: = ', bottom - top, '\n'
    return im.getbbox()

def get_sign_bbx_by_doc(doc, signid, name_obj, options):
    '''prepare sign board'''

    sign_root  = doc.find(r'{http://www.w3.org/2000/svg}g')

    for sign in doc.findall(r'{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}g'):
        sign_id_str = sign.attrib['id'].upper()
        if sign_id_str != signid:
            sign.attrib['opacity'] = '0.0'
        else:
            sign.attrib['opacity'] = '1.0'

    outfile = os.path.join(options.outdir,name_obj.fn + "_" + signid + '_TMP' + name_obj.ext)

    write_svg_with_pi(doc, outfile)

    tmp_path = os.path.join(options.outdir, 'TMP')
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    name = '%s_%s_TMP_d.PNG' % (name_obj.fn, signid)
    pngfile = os.path.join(tmp_path, name)

    run_batik_rasterizer(outfile, pngfile, g_default_width, g_default_height)
    im = Image.open(pngfile)

    return im.getbbox()

def run_batik_rasterizer(outfile, pngfile, width, height):
    '''run batik rasterizer process'''

    widthparam = ""
    heightparam = ""

    if width > 0:
        widthparam = "-w %d " % width
    if height > 0:
        heightparam = "-h %d " % height

    proc = r'java.exe -jar .\batik-1.7\batik-rasterizer.jar'
    param = ' %s %s -d %s %s' % (widthparam, heightparam, pngfile, outfile)
    os.system(proc + param)


def crop_portrait(im, sign_left, sign_right):
    (width, height) = im.size
    (left, top, right, bottom) = im.getbbox()
    #print 'crop portrait:', sign_left, sign_right
    #highlight panel bbx < 460
    if sign_right - sign_left < g_portrait_width:

        #left has white space, if all bbx is small than 460
        if right - left <= g_portrait_width:
            startx = right - g_portrait_width
            if startx < 0:
                startx = 0
            im = im.crop((int(startx), top, int(startx + g_portrait_width), bottom))

        #sign panel bbx > portrait_width, need to cut
        else:
            gap = g_portrait_width - (sign_right - sign_left)
            gap = int(gap / 2.0)
            left_crop = sign_left - left
            right_crop = right - sign_right

            if left_crop < gap:
                im = im.crop((left, top, left + int(g_portrait_width), bottom))
            elif right_crop < gap:
                im = im.crop((right - int(g_portrait_width), top, right, bottom))
            else:
                im = im.crop((sign_left - gap, top, sign_right + gap, bottom))
    #bbx > portrait_width
    else:
        im = im.crop((sign_left, top, sign_right, bottom))
    return im

def calculate_offset(panel_factor, svg_factor, left, top, right, bottom):
    #svg_factor = 1.0
    #all svg is 640x480 now, we add 100 pixel to left and 100 to right
    original_width = IMAGE_WIDTH
    original_height = IMAGE_HEIGHT
    addhalf = g_addHalf
    adding_width = addhalf * 2

    center_x = (left + right) / 2.0
    #print 'svg_factor:', svg_factor
    new_l = addhalf * svg_factor + (left  - addhalf) * panel_factor
    new_r = addhalf * svg_factor + (right - addhalf) * panel_factor
    center_new = (new_l + new_r) / 2.0

    deltax = (center_x - center_new) / (panel_factor * svg_factor)
    deltay = (top - top * panel_factor) / (panel_factor * svg_factor)

    return (deltax, deltay, new_l, new_r)

def combination(doc, signsrect):
    c_bbx_left = 10000
    c_bbx_right = 0
    for (signid, (left, top, right, bottom)) in signsrect:
        #sar bbx
        if c_bbx_left > left:
            c_bbx_left = left
        if c_bbx_right < right:
            c_bbx_right = right
    c_bbx_width = c_bbx_right - c_bbx_left
    for (signid, (left, top, right, bottom)) in signsrect:
        if (c_bbx_width - right + left) < 10:
            return True
    return False
        

def highlight_panel(options, doc, meta_map, pvid_src, metak, refids_gather, panel_factor, deltax, deltay, signsrect):

    sign_root = doc.find(r'{http://www.w3.org/2000/svg}g')
    assert (sign_root != None)

    signscombination = False
    if len(meta_map) > 1:
        signscombination = combination(doc, signsrect)
        
    for sign in doc.findall(r'{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}g'):	
        PanelForTwoDirection = False
        sign_highlight = False
#start change by simon 20130514
#PanelForTwoDirection = True
#end change by simon 20130514

        #For two direction situation
        inner = False
        outer = False
        for ids in sign.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'): 
            if ids.attrib['id'] in meta_map[(pvid_src, metak)]:
                inner = True
                sign_highlight = True
            elif ids.attrib['id'] in refids_gather:
                outer = True
                ids.attrib['opacity'] = '0.5'
		
        if (inner and outer) or (signscombination == True):
            PanelForTwoDirection = True
			
        for ids in sign.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
            if ('type' in ids.attrib) and (ids.attrib['type'] == 'Panel'):
                if PanelForTwoDirection == True:
                    if 'opacity' in ids.attrib:
                        del ids.attrib['opacity']
                        for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                            child_ids.attrib['opacity'] = '0.5'
                else:
                    opac = True
                    for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                        if not 'opacity' in child_ids.attrib:
                            opac = False
                            break
                    if opac == True:
                        for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                            del child_ids.attrib['opacity']
                        ids.attrib['opacity'] = '0.5'
					
        for ids in sign.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
            if ('type' in ids.attrib) and (ids.attrib['type'] == 'Panel'):
                if 'opacity' in ids.attrib:
                    for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                        if 'opacity' in child_ids.attrib:
                            del child_ids.attrib['opacity']		
                if ids.attrib['id'] in meta_map[(pvid_src, metak)]:
                    for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                        if 'opacity' in child_ids.attrib:
                            del child_ids.attrib['opacity']
                elif ids.attrib['id'] in refids_gather:
                    for child_ids in ids.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                        if child_ids.attrib['id'] in meta_map[(pvid_src, metak)]:
                            if 'opacity' in child_ids.attrib:
                                del child_ids.attrib['opacity']								
            elif ('type' in ids.attrib) and (ids.attrib['type'] == 'Background') and ('opacity' in ids.attrib):		
                if PanelForTwoDirection == True:
                    del ids.attrib['opacity']
			
        if (sign_highlight == True) or (signscombination == True):
            #enlarge highlight
            transform_attr = 'scale(%f, %f) translate(%f, %f)' % (panel_factor, panel_factor, deltax, deltay)
            sign.attrib['transform'] = transform_attr
            new_sign = copy.deepcopy(sign)
            #add white border
            if options.frame_color > 0:
                sign.attrib['style'] = STYLE_ATTRIB_RED
            else:
                sign.attrib['style'] = STYLE_ATTRIB_WHITE
            #add close for path
            for ele in sign.getiterator():
                if ele.tag == r'{http://www.w3.org/2000/svg}path':
                    data = ele.get('d')
                    if not data.endswith('z'):
                        ele.attrib['d'] = data + 'z'
			
            if signscombination == False:			
                sign_root.remove(sign)
                sign_root.append(sign)
            sign_root.append(new_sign)

    return doc

def verify_sar(im):
    (width, height) = im.size
    border = 255 * 4
    border_l = -1
    border_r = -1
    start_h = height / 4
    end_h = start_h * 3
    #find border
    for i in range(start_h, end_h):
        pix = (0, i)
        (r, g, b, a) = im.getpixel(pix)
        total = r + g + b + a
	if a == 255:
	    if total < border:
                print '!!!!!!!!!!!!!!!!!!!!!!error: why we cannot find the left border of highlight panel?'
		print 0, i, total
                return -1
    for i in range(start_h, end_h):
        pix = (width - 1, i)
        (r, g, b, a) = im.getpixel(pix)
        total = r + g + b + a
	if a == 255:
	    if total < border:
		print width - 1, i, total
                print '!!!!!!!!!!!!!!!!!!!!!!error: why we cannot find the right border of highlight panel?'
                return -1
    return 0

#hleft, htop, hright, hbottom is original panel bbx
def create_portrait(lpngfile, signid, nameobj, options, doc, sar_bbx_height, sarsize, signsrect, meta_map, pvid_src, metak, refids_gather):
    ''' clipping png files'''

    pngfile = lpngfile.replace('.PNG', '_P.PNG')

    svg_factor = 1.0
    panel_factor = 2.0

    factor_w = 1.0
    factor_h = 1.0

    panel_width = sarsize.right - sarsize.left
    panel_height = sar_bbx_height

    factor_w = 460.0 / panel_width
    factor_h = MAX_PORTRAIT_HEIGHT / panel_height

    factor = min(factor_w, factor_h)
    if factor > 2.0:
        panel_factor = MAX_PORTRAIT_SCALE
        svg_factor = factor / panel_factor
    else:
        panel_factor = factor
        svg_factor = 1.0


    (deltax, deltay, new_l, new_r) = calculate_offset(panel_factor, svg_factor, sarsize.left, sarsize.top, sarsize.right, sarsize.bottom)
    new_w = g_default_width * svg_factor
    new_h = g_default_height* svg_factor

    highlight_panel(options, doc, meta_map, pvid_src, metak, refids_gather, panel_factor, deltax, deltay, signsrect)

    outfile = nameobj.get_svg_name(signid, options)
    #doc.write(outfile)
    write_svg_with_pi(doc, outfile)

    run_batik_rasterizer(outfile, pngfile, new_w, new_h)
    im = Image.open(pngfile)

    (png_width, png_height) = im.size
    (png_left, png_top, png_right, png_bottom) = im.getbbox()
    crop_width = min(png_left, png_width - png_right)
    im = im.crop((crop_width, png_top, png_width - crop_width, png_bottom))
    im.save(pngfile)
    (width, height) = im.size

    if width <= g_portrait_width:
        if height != MAX_PORTRAIT_HEIGHT:
            im = im.resize((width, int(MAX_PORTRAIT_HEIGHT)), Image.ANTIALIAS)
        im.save(pngfile)
        return

    middle_h = height / 2
    border_l = -1
    border_r = -1
    #find border
    for i in range(0, width):
        (r, g, b, a) = im.getpixel((i, middle_h))
        if a == 255:
            if border_l == -1:
                border_l = i
            else:
                border_r = i
    if border_l == -1:
        print '!!!!!!!!!!!!!!!!error: why we cannot find the left border of highlight panel?', pngfile
    if border_r == -1:
        print '!!!!!!!!!!!!!!!!error: why we cannot find the right border of highlight panel?', pngfile

    #panel small the 460
    #if border_r - border_l < g_portrait_width:
    #    if height < g_max_height:
    #        im = im.resize((width, int(g_max_height)))
    border_r = border_r + 2
    im = crop_portrait(im, border_l, border_r)
    (width, height) = im.size

    if width > g_portrait_width:
        height = height * g_portrait_width / width
        if height > MAX_PORTRAIT_HEIGHT:
            height = MAX_PORTRAIT_HEIGHT
        im = im.resize((int(g_portrait_width), int(height)), Image.ANTIALIAS)
    elif height != MAX_PORTRAIT_HEIGHT:
        im = im.resize((width, int(MAX_PORTRAIT_HEIGHT)), Image.ANTIALIAS)

    im.save(pngfile)
	
def save_png_file(signid, nameobj, options, doc, doc_org, sar_bbx_height, sarsize, signsrect, error_sar_counter, error_log, meta_map, pvid_src, metak, refids_gather):
    #start to convert
    outfile = nameobj.get_svg_name(signid, options)
    #doc.write(outfile)
    write_svg_with_pi(doc, outfile)
    pngfile = nameobj.get_png_name(signid, options)			
    run_batik_rasterizer(outfile, pngfile, sarsize.new_w, sarsize.new_h)

    #land scape mode
    im = Image.open(pngfile)
    (png_width, png_height) = im.size
    (png_left, png_top, png_right, png_bottom) = im.getbbox()
    crop_width = min(png_left, png_width - png_right)
    im = im.crop((crop_width, png_top, png_width - crop_width, png_bottom))
    (png_width, png_height) = im.size
    im.save(pngfile)
	
    if png_width > g_landscape_width:
        print '---warning: a sar is more than 780: ' + pngfile
        png_height = png_height * g_landscape_width / png_width
        if png_height > MAX_LANDSCAPE_HEIGHT:
            png_height = MAX_LANDSCAPE_HEIGHT
        im = im.resize((int(g_landscape_width), int(png_height)))
        im.save(pngfile)
    elif png_height > MAX_LANDSCAPE_HEIGHT:
        im = im.resize((png_width, int(MAX_LANDSCAPE_HEIGHT)))
        im.save(pngfile)

    vresult = verify_sar(im)
    
    if vresult < 0:
        print 'error for this:', pngfile 
        error_sar_counter = error_sar_counter + 1
        info = 'Error: clop error:%s\n' % pngfile
        error_log.write(info)
	
    if options.portrait:
        doc = copy.deepcopy(doc_org)
        doc.getroot().attrib['width'] = '1600px';
        create_portrait(pngfile, signid, nameobj, options, doc, sar_bbx_height, sarsize, signsrect, meta_map, pvid_src, metak, refids_gather)
		
    return error_sar_counter
	
def process_sar_file(filename, error_log, options):

    error_sar_counter = 0
	
    if options.verbose:
        print "Processing: %s" % filename

    nameobj = NameObject(filename)
	
    try:
      doc_org = ET.parse(filename)
    except:
      info = 'Error: can not parse:%s\n' % filename
      error_log.write(info)
      raise
     
    if options.original_png:
        outfile = nameobj.get_svg_name('org', options)
        write_svg_with_pi(doc_org, outfile)
        pngfile = nameobj.get_png_name('org', options)
        run_batik_rasterizer(outfile, pngfile, IMAGE_WIDTH, IMAGE_HEIGHT)

    doc = copy.deepcopy(doc_org)
    doc.getroot().attrib['width'] = '1600px';

    sar_bbx_left = sar_bbx_top = 10000
    sar_bbx_right = sar_bbx_bottom = 0
    
    signsrect = set()
    for sign in doc_org.findall(r'{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}g'):
        signid = sign.attrib['id']
        (left, top, right, bottom) = get_sign_bbx_by_doc(doc, sign.attrib['id'], nameobj, options)
        signsrect.add((signid, (left, top, right, bottom)))
        #sar bbx
        if sar_bbx_left > left:
            sar_bbx_left = left
        if sar_bbx_top > top:
            sar_bbx_top = top
        if sar_bbx_right < right:
            sar_bbx_right = right
        if sar_bbx_bottom < bottom:
            sar_bbx_bottom = bottom
    sar_bbx_height = sar_bbx_bottom - sar_bbx_top
    crop_w_org = min(sar_bbx_left - g_addHalf, IMAGE_WIDTH + g_addHalf - sar_bbx_right)
    sar_c_width = IMAGE_WIDTH - 2 * crop_w_org
	
    meta_map = {}
    refids_gather = set()
    for routes in doc_org.findall(r'{http://www.navteq.com/SaR3/1.0}routes'):
        pvid_src = routes.get('sourceLinkPVId', 'Invalid Source PVID')
        pvid_dst = ''
        for route in routes.findall(r'{http://www.navteq.com/SaR3/1.0}route'):
            pvid_dst = route.get('destinationLinkPVId', 'Invalid Destination PVID')
            ref_ids = set()
            for object in route.findall(r".//{http://www.navteq.com/SaR3/1.0}SVGObject"):
                ref_ids.add(object.attrib['refId'])		
                refids_gather.add(object.attrib['refId'])						
						
            meta_map[(pvid_src, pvid_dst)] = ref_ids
					
    directions = 1
    for metak, metav in meta_map.items():
	
        #landscape mode
        panel_factor = MAX_LANDSCAPE_SCALE
        svg_factor = 1.0

        #calculate svg_factor
        if sar_bbx_height > MAX_LANDSCAPE_HEIGHT:
            svg_factor = MAX_LANDSCAPE_HEIGHT / (sar_bbx_height * panel_factor)
        else:
            new_height = sar_bbx_height * panel_factor
            if new_height > MAX_LANDSCAPE_HEIGHT:
                panel_factor = MAX_LANDSCAPE_HEIGHT / sar_bbx_height
            else:
                svg_factor = MAX_LANDSCAPE_HEIGHT / new_height
			
        vsign = []			
        for sign in doc_org.findall(r'{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}g'):
            for ids in sign.findall(r'.//{http://www.w3.org/2000/svg}g[@id]'):
                if ids.attrib['id'] in meta_map[(pvid_src, metak[1])]:
                    vsign.append(sign.attrib['id'])
                    break
		
        
        if not vsign:
            directions = directions + 1
            continue
        pleft = ptop = 10000
        pright = pbottom = 0
        for (signid, (left, top, right, bottom)) in signsrect:
            if signid in vsign:
                if pleft > left:
                    pleft = left
                if ptop > top:
                    ptop = top
                if pright < right:
                    pright = right
                if pbottom < bottom:
                    pbottom = bottom
	
        if len(meta_map) > 1:
            signscombination = combination(doc_org, signsrect)
        else:
            signscombination = False
        
        if signscombination == True:
            pleft = sar_bbx_left
            pright = sar_bbx_right
            ptop = sar_bbx_top
            pbottom = sar_bbx_bottom
		
        if panel_factor > 1:
            added_width = (pright - pleft) * (panel_factor - 1) / 2.0

            added_width_r = pright + added_width - IMAGE_WIDTH - g_addHalf 
            if added_width_r < 0:
                added_width_r = 0
            added_width_l = pleft - (added_width + g_addHalf)
            if added_width_l < 0:
                added_width_l = (added_width + g_addHalf) - pleft
            else:
                added_width_l = 0
			
            #after enlarment, maybe it will go out of the window
            extent_width = max(added_width_l, added_width_r)
            #what is the exact width after processing?
            new_width = extent_width * 2.0 + sar_c_width
            #print svg_factor, new_width, new_width * svg_factor
            if new_width * svg_factor > g_landscape_width:
                svg_factor = g_landscape_width / float(new_width)
                if svg_factor < 0.8:
                    print 'notice: here is a special cases like 91512'
                    panel_factor = panel_factor * svg_factor
                    svg_factor = 1.0

        sarsize = item()
        (deltax, deltay, new_l, new_r) = calculate_offset(panel_factor, svg_factor, pleft, ptop, pright, pbottom)
        sarsize.new_w = g_default_width * svg_factor
        sarsize.new_h = g_default_height* svg_factor
        sarsize.left = pleft
        sarsize.right = pright
        sarsize.top = ptop
        sarsize.bottom = pbottom
		
        doc = copy.deepcopy(doc_org)
        doc.getroot().attrib['width'] = '1600px';
        highlight_panel(options, doc, meta_map, pvid_src, metak[1], refids_gather, panel_factor, deltax, deltay, signsrect)
        signid = '%s%s' % ('SIGN_L1R1_', directions)
        directions = directions + 1

        save_png_file(signid, nameobj, options, doc, doc_org, sar_bbx_height, sarsize, signsrect, error_sar_counter, error_log, meta_map, pvid_src, metak[1], refids_gather)

    print 'notice this, clop error sar:', error_sar_counter


def traverse_dir(rootdir):
    lists = []
    for path, dirs, files in os.walk(rootdir):
        for file_ in files:
            if file_.endswith('.svg'):
                fullpath = os.path.join(path, file_)
                lists.append(fullpath)

    return lists

def get_options(args=None):
    """setup and get options"""
    usage = "usage: %prog [options] svgfiles(s)"
    parser = OptionParser(usage)

    parser.add_option('-v','--verbose',action="store_true", dest="verbose", default=False)
    parser.add_option('-x','--width',action="store", type="int", dest="width", default=780)
    parser.add_option('-y','--height',action="store", type="int", dest="height", default=160)
    parser.add_option('--maxw',action="store", type="int", dest="maxw", default=460)
    parser.add_option('--maxh',action="store", type="int", dest="maxh", default=MAX_PORTRAIT_HEIGHT)
    parser.add_option('-d','--outputdir',action="store", dest="outdir", default=".")
    parser.add_option('-f','--frame',action="store", type="int", dest="frame_color", default=0)
    parser.add_option('-c','--threadcount',action="store",type="int", dest="thread", default=6, help="thread count")
    parser.add_option('-l','--log_only',action="store_true", dest="lo", default=False)
    parser.add_option('-p', '--portrait_mode', action="store_true", dest="portrait", default=False)
    parser.add_option('-t', '--test_mode', action="store_true", dest="original_png", default=False)
    parser.add_option('-m', '--delete tmp files', action="store_true", dest="clear_tmp", default=False)

    (options, svg_file_specs) = parser.parse_args(args)
    if len(svg_file_specs) < 1:
        parser.error("Please specify the directory of the file to be processed.")

    return options, svg_file_specs

def main(argv=None):

    (options, svg_file_specs) = get_options(argv)

    svg_files = list(file for file_spec in svg_file_specs for file in glob.glob(file_spec))

    tmp_path = os.path.join(options.outdir, 'TMP')
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    begin = clock()
    
    #open log for write dowm error info
    error_log = open(os.path.join(options.outdir, 'error.log'), 'w')
    
    for svg_dir in svg_files:
        file_list = traverse_dir(svg_dir)

        if options.lo: #only log files mode
            for svg_file in file_list:
                process_sar_ennv_log_file(svg_file, error_log, options)
        else:
          #copy customcolors.css to out directory first
          if file_list:
            dir, name = os.path.split(file_list[0])
            css_path = os.path.join(os.path.abspath(dir), '../../customcolors.css')
            if os.path.exists(css_path):
              shutil.copy(css_path, options.outdir)
            else:
              print "Error: can't find customcolors.css %s" % css_path
              return 0
            
            wm = WorkerManager(options.thread, 8)
            for svg_file in file_list:
                wm.add_job( process_sar_file, svg_file, error_log, options)
            wm.wait_for_complete()
            
            #delete tempratory *.svg files
            if options.clear_tmp:
                tmp_dir = os.path.join(options.outdir, 'TMP')
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)

                for svg in traverse_dir(options.outdir):
                    try:
                        os.remove(svg)
                    except:
                        continue

    error_log.write('errors?\n if there are something wrong, send this to Myao')
    error_log.close()
    
    hour = (int(clock()-begin)) / 3600
    minute = (int(clock()-begin) % 3600) / 60
    second = (int(clock()-begin)) % 60
    print "Elapsed Time: %02d:%02d:%02d" % (hour, minute, second)

if __name__ == '__main__':
    main()
