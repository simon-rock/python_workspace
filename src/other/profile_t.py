def foo():
    sum = 0
    for i in range(1000000):
        sum += i
    return sum


import time
def fast():
    time.sleep(0.001)
def slow():
    time.sleep(0.01)
def very_slow():
    for i in xrange(100):
        fast()
        slow()
    time.sleep(0.1)

def main():
    very_slow()
    very_slow()
if __name__ == "__main__":
    import profile
    profile.run("main()", "run.log")
    import pstats
    p = pstats.Stats("run.log").strip_dirs()
    p.sort_stats("time").print_stats()
    #main()                  # run useage: python -m profile profile_t.py  or python -m cProfile profile_t.py
