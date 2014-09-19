#!/usr/bin/env python
#coding: utf-8
#encoding: utf-8
import cairo
import gtk
import math
import glib
import random
 
class MainWindow(gtk.Window):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.init_ui()
        self.load_image()
        self.init_vars()
 
    def init_ui(self):
        self.darea = gtk.DrawingArea()
        self.darea.connect("expose_event", self.expose)
        self.add(self.darea)
         
        glib.timeout_add(100, self.on_timer)
 
        self.set_title("Clipping")
        self.resize(300, 200)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete-event", gtk.main_quit)
        self.show_all()
 
    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.on_draw(300, self.context)
         
    def on_draw(self, wdith, cr):
        w, h = self.get_size()
         
        if (self.pos_x < 0 + self.radius):
            self.delta[0] = random.randint(5, 9)
        elif (self.pos_x > w - self.radius):
            self.delta[0] = - random.randint(5, 9)
             
        if (self.pos_y < 0 + self.radius):
            self.delta[1] = random.randint(5, 9)
        elif (self.pos_y > h - self.radius):
            self.delta[1] = - random.randint(5, 9)
             
        cr.set_source_surface(self.image, 1, 1)
        cr.arc(self.pos_x, self.pos_y, self.radius, 0, 2 *math.pi)
        cr.clip()
        x1 = 0
        y1 = 0
        x2 = 0
        y2 = 0
        (x1, y1, x2, y2) = cr.clip_extents()
        print "result : ", x1, y1, x2, y2, "(", self.pos_x, self.pos_y, self.radius, ") -- ", x2-x1, y2-y1
        cr.paint()
         
    def load_image(self):
        self.image = cairo.ImageSurface.create_from_png("tree_png.png")
         
    def init_vars(self):
        self.pos_x = 128
        self.pos_y = 128
        self.radius = 40
         
        self.delta = [3, 3]
         
    def on_timer(self):
        self.pos_x += self.delta[0]
        self.pos_y += self.delta[1]
        self.darea.queue_draw()
        return True;
 
def main():
    window = MainWindow()
 
    gtk.main()
         
if __name__ == "__main__":
    main()
