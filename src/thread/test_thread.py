import threading
from threading import Thread

import time

class Test(Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.__run_num = num

    def run(self):
        global count, mutex
        threadname = threading.currentThread().getName()

        for x in xrange(0, int(self.__run_num)):
            mutex.acquire()
            count = count + 1
            mutex.release()
            print threadname, x, count
            time.sleep(1)

if __name__ == '__main__':
    global count, mutex
    threads = []
    num = 4
    count = 1

    mutex = threading.Lock()

    for x in xrange(0, num):
        threads.append(Test(10))

    for t in threads:
        t.start()

    for t in threads:
        t.join()
