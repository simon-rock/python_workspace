permissions = 'rw'
print 'w' in permissions
print 'x' in permissions
user = ['mlh', 'foo', 'bar']
print user
print 'asdf'

print "-------------------------"
format = "Pi with three decimals: %.3f"
from math import pi
print format % pi

print "-------------------------"
from string import Template
s = Template('$x. glorious $x!')
print s.substitute(x = 'slurm')
print "-----------ex 1--------------"

class MyTemplate(Template):
	"""docstring for Mytemplate"""
	delimiter = '#'

def _test():
	s = '#who likes #what'
	t = MyTemplate(s)
	d = {'who': 'jianpx', 'what':'mac'}
	print t.substitute(d)
	print MyTemplate.delimiter
	print Template.delimiter

	s_ori = '$who likes $what'
	t_ori = Template(s_ori)
	print t_ori.substitute(d)

if __name__ == '__main__':
	_test()
