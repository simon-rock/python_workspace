def getpixel(i):
    return (i , i+1, i+2, i+3)

def main():
    for i in range(1, 10):
        print i
        (r, g, b, a) = getpixel(i)
        total = r + g + b + a
    if a == 11:
        print total


if __name__ == "__main__":
    main()
