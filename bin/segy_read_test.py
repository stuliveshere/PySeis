#!/usr/bin/env python2.7
import PySeis.segy as d
import PySeis.misc as c
import PySeis.h5 as h
import PySeis.su as su
import numpy as np
import matplotlib.pyplot as pylab
import tables as tb
import time
import os


#~ #open stuff 
os.chdir('../data')
input = 'sample.sgy'

#~ input = [file for file in os.listdir('.') if '.sgy' in file]

#open database
h5 = h.h5(filename='test.h5')



#initialise project. this time it will be a separate project per file
for file in input:
	with open(input, 'rb') as f:
		f.seek(3600)
		ns = np.array(f.read(240), dtype=d.segy_trace_header_dtype)['ns']
		h5.init(input.split('.')[0], ns=ns, segy=True)
		
		#~ f.seek(0)
		#read in EBCDIC header and write to table
		#~ fh = f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
		#~ h5.fh.append(np.fromstring(fh, dtype=d.segy_textual_header_dtype))
		
		#repeat for binary header
		#~ bh = f.read(400)	
		#~ bh = np.fromstring(bh, dtype=d.segy_binary_header_dtype).byteswap()
		#~ h5.bh.append(bh)
		
		#read in trace headers and traces
		#~ for chunk in iter(lambda: f.read(240), ""):
			#~ th = np.fromstring(chunk, dtype=d.segy_trace_header_dtype).byteswap()
			#~ h5.th.append(th)
			#~ td = c.ibm2ieee(np.fromfile(f, dtype='>i4', count=ns)).reshape(1,ns)
			#~ td = np.fromfile(f, dtype='>f4', count=ns).reshape(1,ns)
			#~ h5.td.append(td)
		



#how to write out h5 table
#~ output = '../data/test.sgy'
#~ with open(output, 'wb') as f:
	#write EBCDIC header
	#~ tfh = h5file.root.line1.FH[0].tostring()
	#~ f.write(tfh.encode('EBCDIC-CP-BE'))
	
	#write binary header
	#~ h5file.root.line1.BH[0].astype(d.segy_binary_header_dtype).tofile(f)
	
	#write trace headers and traces
	#~ for trace in range(h5file.root.TH.nrows):
		#~ print h5file.root.TH[trace]
		#~ h5file.root.line1.TH[trace].astype(d.segy_trace_header_dtype).tofile(f)
		#~ print h5file.root.TD[trace]
		#~ h5file.root.line1.TD[trace].astype('>f4').tofile(f)
		

	


	


