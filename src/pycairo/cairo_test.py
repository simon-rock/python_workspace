#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import cairo
import cairosvg
import os
import gtk

#http://my.oschina.net/wolfcs/blog/131874
def process_png():
    ims = cairo.ImageSurface(cairo.FORMAT_ARGB32, 390, 60)
    cr = cairo.Context(ims)

    cr.set_source_rgb(0,0,0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(40)
     
    cr.move_to(10, 50)
    cr.show_text("Diszip ist Macht.")
    print ims.get_height(), ims.get_width(),ims.get_stride()
    ims.write_to_png("image.png")

def process_pdf():
    ps = cairo.PDFSurface("pdffile.pdf", 504, 648);
    cr = cairo.Context(ps)
     
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(40)
     
    cr.move_to(10, 50)
    cr.show_text("Diszip ist Macht.")
    cr.show_page()

def process_svg():
    ps = cairo.SVGSurface("svgfile.svg", 390, 60);
    cr = cairo.Context(ps)
     
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(40)
     
    cr.move_to(10, 50)
    cr.show_text("Diszip ist Macht.")
    cr.show_page()
    
class Example(gtk.Window):
    def __init__(self):
        print "init"
        super(Example, self).__init__()
        self.init_ui()
        print "Example: " + str(self)
         
    def init_ui(self):
        print "init_ui"
        darea = gtk.DrawingArea()
        darea.connect("expose_event", self.expose)
        self.add(darea)
 
        self.set_title("GTK window")
        self.resize(420, 120)
        self.set_position(gtk.WIN_POS_CENTER)
        print "set_position"
        self.connect("delete-event", gtk.main_quit)
        print "connect"
        self.show_all()
        print "show all"
         
    def expose(self, widget, event):
        print "expose"
        self.context = widget.window.cairo_create()
        #self.context
        self.on_draw(420, self.context)
        print "expose: " + str(widget)
         
    def on_draw(self, wid, cr):
        print "on_draw"
        cr.set_source_rgb(0, 0, 0)
        print "error?"
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(40)
     
        cr.move_to(10, 50)
        print "move to"
        cr.show_text("Diszip ist Macht.")
        
def process_gtk():
    print "process_gtk"
    window = Example()
    gtk.main()
    
# http://www.jb51.net/article/54125.htm
def svg2png():
    fromDir = "source_data"
    targetDir = "output"
    exportType = "png"
    files = os.listdir(fromDir)
    print files
    for fileName in files:
        path = os.path.join(fromDir,fileName)
        print path
        if os.path.isfile(path) and fileName[-3:] == "svg":
            fileHandle = open(path)
            svg = fileHandle.read()
            fileHandle.close()
            exportPath = os.path.join(targetDir, fileName[:-3] + exportType)
            exportFileHandle = open(exportPath,'w')
        
            if exportType == "png":
                cairosvg.svg2png(bytestring=svg, write_to=exportPath)
            elif exportType == "pdf":
                cairosvg.svg2pdf(bytestring=svg, write_to=exportPath)
            
            exportFileHandle.close()

def singlesvg2svg(fileName):
    fromDir = "source_data"
    targetDir = "."
    exportType = "png"
    path = os.path.join(fromDir,fileName)
    print path
    if os.path.isfile(path) and fileName[-3:] == "svg":
        fileHandle = open(path)
        svg = fileHandle.read()
        fileHandle.close()
        exportPath = os.path.join(targetDir, fileName[:-3] + exportType)
        exportFileHandle = open(exportPath,'w')
        
        if exportType == "png":
            cairosvg.svg2png(bytestring=svg, write_to=exportPath)
        elif exportType == "pdf":
            cairosvg.svg2pdf(bytestring=svg, write_to=exportPath)            
        exportFileHandle.close()

if __name__ == "__main__":
    #process_png()
    #process_pdf()
    #process_svg()
    #process_gtk()
    svg2png()
    #singlesvg2svg("group.svg")
