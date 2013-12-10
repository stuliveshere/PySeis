import numpy as np
import PySeis.segd.definitions as d

class segdReader():
	'''
	reads all headers into holding dictionaries.
	generates file layout dictionary
	so traces can be read in with ease.
	'''
	def __init__(self, filename):
		self.handle = open(filename, 'rb')
		print self.read_general_header_1()
		
		
	def read_general_header_1(self):
		self.handle.seek(0)
		bytes = np.fromfile(self.handle, dtype=np.uint8, count=32)
		nibbles = self.bcd(bytes)
		datastore = {}
		indice = 0
		for key, value in d.segd_general_header_list:
			x =  nibbles[indice:indice+value]
			indice += value
			datastore[key] = ''.join(x)
		if datastore['format'] not in d.segd_allowed_formats:
			#raise exception
			pass
		return datastore
		
	def read_general_header_2(self):
		pass
		
	def read_scan_header(self):
		pass
		
	def read_trace_header(self):
		pass
	
	def bcd(self, uints):
		n = uints & 0xf
		m =  (uints  >> 4) & 0xf
		return np.dstack([m, n]).flatten().astype('S2')	
	

		#~ header = {}


		#~ print header
		
if __name__ == '__main__':
	a = segdReader('../data/sample.segd')

