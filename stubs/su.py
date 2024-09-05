'''
	To do:
		test for endianness by checking for sane values, store in flag

	Use:
		data = SU("/path/to/inputFile.su")
		data.read("/path/to/raw.npy")
'''

import numpy as np, sys, os
import mmap
from .headers import su_trace_header
from .tools import pack_dtype
import pprint

	
class SU(object):
	'''
	reading and writing SU files, including those larger than RAM,
	to and from .npy files
	'''
	def __init__(self, _file):
		self.params = {}
		self._file = self.params['filename'] = _file
		self.readNS()
		self.report()

	def readNS(self):
		header_dtype =  pack_dtype(values=su_trace_header)
		header = np.fromfile(self._file, dtype=header_dtype, count=1)
		self.ns = header['ns'][0]
		self.params["ns"] = self.ns
		self._dtype = pack_dtype(values=su_trace_header + [('trace', (np.float32, self.ns), 240)])
		
	def report(self):		
		pprint.pprint(self.params)
		
	def read(self):
		'''
		reads a SU file to a .npy file
		'''
		self.gathers= np.memmap(self._file, dtype=self._dtype, mode='r+')
	
	def write(self, _inline,_outfile):
		'''
		writes a .npy file to a SU file
		'''
		npyFile = np.memmap(_infile, dtype=self._dtype, mode='r')


	
	

	



