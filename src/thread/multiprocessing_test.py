#coding: utf-8

#http://blog.ftofficer.com/2009/12/python-multiprocessing-3-about-queue/
import multiprocessing

def run(a, b, c):
    print a, b, c 
    #pass

p = multiprocessing.Process(target=run, args=(1,2,3))
p2 = multiprocessing.Process(target=run, args=(2,3,4))
p.start()
p2.start()
p.join()
p2.join()


