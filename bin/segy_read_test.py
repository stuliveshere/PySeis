#!/usr/bin/env python2.7
import  PySeis.segy as d
import PySeis.misc as c
import PySeis.su as su
import numpy as np
import matplotlib.pyplot as pylab
import tables as tb
import time


#open stuff 
file = '../data/sample.sgy'


#initialise database
h5file = tb.openFile("../data/test1.h5", mode = "w", title = "Test file")
line1 = h5file.createGroup("/", 'line1', 'Line 1 Survey')
file_header = h5file.createTable(line1, 'FH', d.segy_file_header, "EBCDIC File Header")
binary_header = h5file.createTable(line1, 'BH', d.segy_binary_header_dtype, "Binary File Header")
trace_header = h5file.createTable(line1, 'TH', d.segy_trace_header_dtype, "Trace Header")

#we really need to reach in and find the number of samples so we can initialise the trace dataset
#first ns will be 40*80 + 400 + 114 = 3714
#or i could be lazy, read the whole of the first trace header and lift out ns

with open(file, 'rb') as f:
	f.seek(3600)
	ns = np.array(f.read(240), dtype=d.segy_trace_header_dtype)['ns']
	
trace_data = h5file.create_earray(     line1,
							name = 'TD',
							atom = tb.Float32Atom(), 
							shape = (0,ns),
							title = "Trace Header", 
							filters = tb.Filters(complevel=5, complib='zlib'))
							


with open(file, 'rb') as f:
	for i in range(40):
		fh = f.read(80).decode('EBCDIC-CP-BE')
		fh = np.fromstring(fh, dtype=(np.str_,   80))
		file_header.append(fh)
		
	bh = f.read(400)	
	bh = np.fromstring(bh, dtype=d.segy_binary_header_dtype).byteswap()
	binary_header.append(bh)
	
	start = time.clock()
	for chunk in iter(lambda: f.read(240), ""):
		th = np.fromstring(chunk, dtype=d.segy_trace_header_dtype).byteswap()
		trace_header.append(th)
		td = np.array([c.ibm2ieee(a) for a in np.nditer(np.fromstring(f.read(ns*4), dtype='>i4'))]).reshape(1,ns) #soooo slow!
		trace_data.append(td)
		print time.clock() - start
		start = time.clock()
		
		h5file.flush()

	




