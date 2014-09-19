#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import gtk
import cairo
 
class MainWindow(gtk.Window):
    def __init__(self):
        print "__init__"
        super(self.__class__, self).__init__()
        self.init_ui()
        self.load_image()
 
    def init_ui(self):
        self.darea = gtk.DrawingArea()
        self.darea.connect("expose_event", self.expose)
        self.add(self.darea)
         
        self.set_title("Image")
        self.resize(300, 170)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete-event", gtk.main_quit)
        self.show_all()
 
    def load_image(self):
        #self.ims = cairo.ImageSurface.create_from_png("stmichaelschurch.png")
        self.ims = cairo.ImageSurface.create_from_png("tree_png.png")
        
 
    def expose(self, widget, event):
        #print "expose"
        self.context = widget.window.cairo_create()
        self.context.paint()
        self.on_draw(300, self.context)
         
    def on_draw(self, wdith, cr):
        cr.set_source_surface(self.ims, 10, 10)
        cr.paint()
 
 
def main():
    window = MainWindow()
    gtk.main()
         
if __name__ == "__main__":
    main()
