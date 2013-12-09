import numpy as np
import PySeis.segd.definitions as d

file = '../data/sample.segd'

def bcd(uints):
	c = np.unpackbits(uints).reshape(-1,4)
	d = np.zeros_like(c)
	e =  np.hstack((d, c))
	f = np.packbits(e)
	f[f == 15] = 0
	return ''.join(f.astype(np.str).tolist())
	

a = open(file, 'r').read(32)
b = np.fromstring(a, dtype=np.uint8)
c = bcd(b)

print np.array(c, dtype = d.segd_general_header)





