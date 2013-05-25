

database = [
	['albert',  '1234'],
	['dilbert', '2345'],
	['smith',   '3456'],
	['jones',   '9843']
]

#username = raw_input('User name: ')
#pin = raw_input('PIN code: ')
username = 'albert'
pin = '1234'

if [username, pin] in database: print 'Access granted'

import sys, pprint
pprint.pprint(sys.path)
#help(pprint)

print pprint.__file__


