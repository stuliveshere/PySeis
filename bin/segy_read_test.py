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
root = h5file.createGroup("/", 'line1', 'Line 1 Survey')
file_header = h5file.createTable("/", 'FH', d.segy_textual_header_dtype, "EBCDIC File Header")
binary_header = h5file.createTable("/", 'BH', d.segy_binary_header_dtype, "Binary File Header")
trace_header = h5file.createTable("/", 'TH', d.segy_trace_header_dtype, "Trace Header")

#~ #we really need to reach in and find the number of samples so we can initialise the trace dataset
#~ #first ns will be 40*80 + 400 + 114 = 3714
#~ #or i could be lazy, read the whole of the first trace header and lift out ns

with open(input, 'rb') as f:
	f.seek(3600)
	ns = np.array(f.read(240), dtype=d.segy_trace_header_dtype)['ns']
	
trace_data = h5file.create_earray(     "/",
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
		td = np.fromfile(f, dtype='>f4', count=ns).reshape(1,ns)
		trace_data.append(td)
		
h5file.flush()

#bit of temporary code to overwrite segy text headers
#~ tfh = open('../templates/EBCDIC.template').readlines()
#~ tfh = ''.join([a.strip().ljust(80) for a in tfh])
#~ print tfh
#~ with open(input, 'r+b') as f:
	#~ f.seek(0)
	#~ f.write(tfh.encode('EBCDIC-CP-BE'))
	
#how to write out h5 table
output = '../data/test.sgy'
with open(output, 'wb') as f:
	#write EBCDIC header
	tfh = h5file.root.FH[0].tostring()
	f.write(tfh.encode('EBCDIC-CP-BE'))
	
	#write binary header
	h5file.root.BH[0].astype(d.segy_binary_header_dtype).tofile(f)
	
	#write trace headers and traces
	for trace in range(h5file.root.TH.nrows):
		#~ print h5file.root.TH[trace]
		h5file.root.TH[trace].astype(d.segy_trace_header_dtype).tofile(f)
		#~ print h5file.root.TD[trace]
		h5file.root.TD[trace].astype('>f4').tofile(f)
		

	


with open(output, 'rb') as f:
	#read in EBCDIC header and write to table
	fh = f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
	file_header.append(np.fromstring(fh, dtype=d.segy_textual_header_dtype))
	
	#repeat for binary header
	bh = f.read(400)	
	#~ print len(bh)
	bh = np.fromstring(bh, dtype=d.segy_binary_header_dtype).byteswap()
	binary_header.append(bh)
	
	#read in trace headers and traces
	#~ for chunk in iter(lambda: f.read(240), ""):
		#~ th = np.fromstring(chunk, dtype=d.segy_trace_header_dtype).byteswap()
		#~ trace_header.append(th)
		#~ td = c.ibm2ieee(np.fromfile(f, dtype='>i4', count=ns)).reshape(1,ns)
		#~ td = np.fromfile(f, dtype='>i4', count=ns).reshape(1,ns)
		#~ trace_data.append(td)

h5file.flush()
	


