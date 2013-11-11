#!/usr/bin/env python2.7
import  PySeis.segy as d
import PySeis.misc as c
import PySeis.su as su
import numpy as np
import matplotlib.pyplot as pylab
import tables as tb
import time


#~ #open stuff 
input = '../data/sample.sgy'


#~ #initialise database
h5file = tb.openFile("../data/test1.h5", mode = "w", title = "Test file")
line1 = h5file.createGroup("/", 'line1', 'Line 1 Survey')
file_header = h5file.createTable(line1, 'FH', d.segy_textual_header_dtype, "EBCDIC File Header")
binary_header = h5file.createTable(line1, 'BH', d.segy_binary_header_dtype, "Binary File Header")
trace_header = h5file.createTable(line1, 'TH', d.segy_trace_header_dtype, "Trace Header")

#~ #we really need to reach in and find the number of samples so we can initialise the trace dataset
#~ #first ns will be 40*80 + 400 + 114 = 3714
#~ #or i could be lazy, read the whole of the first trace header and lift out ns

with open(input, 'rb') as f:
	f.seek(3600)
	ns = np.array(f.read(240), dtype=d.segy_trace_header_dtype)['ns']
	
trace_data = h5file.create_earray(     line1,
							name = 'TD',
							atom = tb.Float32Atom(), 
							shape = (0,ns),
							title = "Trace Header", 
							filters = tb.Filters(complevel=1, complib='zlib'))
							


with open(input, 'rb') as f:
	#read in EBCDIC header and write to table
	fh = f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
	file_header.append(np.fromstring(fh, dtype=d.segy_textual_header_dtype))
	
	#repeat for binary header
	bh = f.read(400)	
	bh = np.fromstring(bh, dtype=d.segy_binary_header_dtype).byteswap()
	binary_header.append(bh)
	
	#read in trace headers and traces
	for chunk in iter(lambda: f.read(240), ""):
		th = np.fromstring(chunk, dtype=d.segy_trace_header_dtype).byteswap()
		trace_header.append(th)
		#~ td = c.ibm2ieee(np.fromfile(f, dtype='>i4', count=ns)).reshape(1,ns)
		td = np.fromfile(f, dtype='>i4', count=ns).reshape(1,ns)
		trace_data.append(td)
		
h5file.flush()

	
#~ a = d.segy()


