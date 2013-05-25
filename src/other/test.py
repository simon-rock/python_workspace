class mem_count:
    mem_static = 0
    def __init__(self):
        self.mem = 1000000
        self.mem += 1
        mem_count.mem_static += 1
    def init(self,j):
        self.mem += j
   

def main():
    m1 = mem_count()
    m1.init(3)

    m2 = mem_count()
    m2.init(4)
    print m1.mem
    print m2.mem
    print mem_count.mem_static

if __name__ == "__main__":
    main()
