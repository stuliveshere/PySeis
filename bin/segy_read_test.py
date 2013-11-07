#!/usr/bin/env python2.7
import  PySeis.segy as d
import PySeis.misc as c
import PySeis.su as su
import numpy as np
import matplotlib.pyplot as pylab

file = open('../data/sample.sgy', 'rb')


for i in range(40):
	file.read(80).decode('EBCDIC-CP-BE') 

#might be a good training step to do this directly in ctypes
	
bh = file.read(400)

bh = np.array(bh, dtype=d.segy_binary_header_dtype)

print bh['format']

#need to figure out how to efficiently decode large quantifies of  ibm 
#floats in files. may need ctypes?

th = file.read(240)

th = np.array(th, dtype=d.segy_trace_header_dtype)

print th['ns']

trace = file.read(2001*4)

trace = np.fromstring(trace, dtype='>i4').tolist()

trace = np.array([c.ibm2ieee(a) for a in trace])
pylab.plot(trace)


data = su.readSU('../data/sample.su')
pylab.plot(data[0]['trace'])


pylab.show()
