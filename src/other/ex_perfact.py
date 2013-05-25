from string import strip, upper
#functions:
#
def map_add(x):
	return x+3

#
if __name__ == '__map_add__':
	map_add(x)

#zip file
def zip_file():
	#open file
	f = open('map.txt')
	lines = f.readlines()
	print lines
	f.close()

	#
	print 'BEFORE\n'
	for eachline in lines:
		print '[%s]' % eachline[:-1]
	#
	print 'AFTER\n'
	for eachline in map(upper, map(strip, lines)):
		print '[%s]' % eachline
	#

if __name__ == '__main__':
	zip_file()
