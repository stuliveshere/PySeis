import numpy as np
import PySeis.segd.definitions as d

file = '../data/sample.segd'

def bcd(uints):
	c = np.unpackbits(uints).reshape(-1,4)
	d = np.zeros_like(c)
	e =  np.hstack((d, c))
	f = np.packbits(e).astype(np.uint8)
	return f
	
def bcd2(uints):
	n = uints & 0xf
	m =  (uints  >> 4) & 0xf
	return np.dstack([m, n]).flatten()	

a = open(file, 'r').read(32)
b = np.fromstring(a, dtype=np.uint8)
c = bcd(b).astype('S').tolist()
print c
r = bcd2(b)

s = d.segd_general_header_list
header = {}

for key, value in s:
	x =  c[:value]
	c = c[value:]
	header[key] = ''.join(x)
print header
	



