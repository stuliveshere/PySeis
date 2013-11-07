#!/usr/bin/env python2.7
import  PySeis.segy as d
import numpy as np

file = open('../data/sample.sgy', 'rb')


for i in range(40):
	file.read(80).decode('EBCDIC-CP-BE') 

#might be a good training step to do this directly in ctypes
	
bh = file.read(400)

bh = np.array(bh, dtype=d.segy_binary_header_dtype)

print bh['format']

#need to figure out how to efficiently decode large quantifies of  ibm 
#floats in files. may need ctypes?

