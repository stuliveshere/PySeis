#initialise a new database
#note the mandatory header is little endian... it is not directly coupled to file IO

import tables as tb
import numpy as np
import time
import PySeis.segy as d

mandatory_header_dtype = np.dtype([
    ('nt', 'u8'), # number of data traces per record
    ('dt', 'f8'), # sample interval in microsecs for this reel
    ('ns', 'u8'), #  number of samples per trace for this reel
   ])  

class h5: #might be better to inheret a pytables object
	def __init__(self, filename, title='PySeis Database'):
		
		#for now we just overwrite with no checks. probably want to change this later.
		self.h5file = tb.openFile(filename, mode = "w", title=title)
		
	def init(self, node, ns, segy=False):
		
		self.node = self.h5file.createGroup("/", node, 'PySeis Node')
		self.mh = self.h5file.createTable(self.node, 'MH', mandatory_header_dtype, "Mandatory Header")
		init = self.mh.row
		init['ns'] = ns
		init.append()
		
		
		self.td = self.h5file.create_earray( self.node,
							name = 'TD',
							atom = tb.Float32Atom(), 
							shape = (0,ns),
							title = "Trace Header", 
							filters = tb.Filters(complevel=1, complib='zlib'),
							expectedrows=100000)
							
		if segy:
			self.fh = self.h5file.createTable(self.node, 'FH', d.segy_textual_header_dtype, "EBCDIC File Header")
			self.bh = self.h5file.createTable(self.node, 'BH', d.segy_binary_header_dtype, "Binary File Header")
			self.th = self.h5file.createTable(self.node, 'TH', d.segy_trace_header_dtype, "Trace Header")
		
		self.h5file.flush()
		


#~ class test(tb.Table):
	#~ def __init__(self, file_name, table_name, description=None,
		#~ group_name='default', mode='a', title="", filters=_filter,
		#~ expectedrows=512000):

		#~ f = tables.openFile(file_name, mode)
	
#~ if __name__ == "__main__":
	#~ a = test()
	#~ a = h5(filename='test.h5')
	