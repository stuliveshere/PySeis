'''
	To do:
		test for endianness by checking for sane values, store in flag

	Use:
		data = SU("/path/to/inputFile.su")
		data.read("/path/to/raw.npy")
'''

import numpy as np, sys, os
import mmap
from .headers import su_header_dtype
import pprint


def memory():
	"""
	Get node total memory and memory usage
	"""
	with open('/proc/meminfo', 'r') as mem:
		ret = {}
		tmp = 0
		for i in mem:
			sline = i.split()
			if str(sline[0]) == 'MemTotal:':
				ret['total'] = int(sline[1])
			elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
				tmp += int(sline[1])
		ret['free'] = tmp
		ret['used'] = int(ret['total']) - int(ret['free'])
		return ret

	
class SU(object):
	'''
	reading and writing SU files, including those larger than RAM,
	to and from .npy files
	'''
	def __init__(self, _file):
		self.params = {}
		self.params['byteswap'] = False
		self._file = self.params['filename'] = _file
		self.readNS()
		self.calculateChunks()
		self.report()

	def readNS(self):
		raw = open(self._file, 'rb').read(240)
		self.ns = ns1 = np.fromstring(raw, dtype=su_header_dtype, count=1)['ns'][0]
		ns2 = np.fromstring(raw, dtype=su_header_dtype, count=1).byteswap()['ns'][0]
		if ns2 < ns1:
			self.params['byteswap'] = True
			self.ns = ns2
		self.params["ns"] = self.ns
		self._dtype = np.dtype(su_header_dtype.descr + [('trace', ('<f4',self.ns))])
		
	def calculateChunks(self, fraction=2):	
		'''
		calculates chunk sizes for SU files that are larger than RAM
		'''
		mem = memory()['free']
		with open(self._file, 'rb') as f:
			f.seek(0, os.SEEK_END)
			self.params["filesize"] = filesize = f.tell() #filesize in bytes
			self.params["tracesize"] = tracesize = 240+self.ns*4.0
			self.params["ntraces"] = int(filesize/tracesize)
			self.params["nchunks"] = nchunks = int(np.ceil(filesize/(mem*fraction))) #number of chunks
			self.params["chunksize"] = chunksize = int((filesize/nchunks) - (filesize/nchunks)%tracesize)
			self.params["ntperchunk"] = int(chunksize/tracesize)
			self.params["remainder"] = filesize - chunksize*nchunks


	def report(self):		
		pprint.pprint(self.params)
		
		
	def read(self, _file):
		'''
		reads a SU file to a .npy file
		'''
		assert self.params['filesize']%self.params['tracesize'] == 0.0
		assert self.params['chunksize']%self.params['tracesize'] == 0.0
		self.outdata = np.memmap(_file, mode='w+', dtype=self._dtype, shape=self.params["ntraces"])
		with open(self._file, 'rb') as f:
			f.seek(0)
			for i in range(self.params["nchunks"]):
				start = int(i*self.params["ntperchunk"])
				end = int((i+1)*self.params["ntperchunk"])
				if self.params['byteswap']: self.outdata[start:end] = np.fromstring(f.read(self.params["chunksize"]).byteswap(), dtype=self._dtype)
				else: self.outdata[start:end] = np.fromstring(f.read(self.params["chunksize"]), dtype=self._dtype)
				self.outdata.flush()
			
			if self.params['byteswap']: self.outdata[end:] = np.fromstring(f.read(self.params["remainder"]).byteswap(), dtype=self._dtype)
			else: self.outdata[end:] = np.fromstring(f.read(self.params["remainder"]), dtype=self._dtype)

			self.outdata.flush()
	
	def write(self, _infile, _outfile):
		'''
		writes a .npy file to a SU file
		'''
		npyFile = np.memmap(_infile, dtype=self._dtype, mode='r')
		npyFile.tofile(_outfile)

if __name__ == "__main__":
	A = SU("../../data/big.su")
	#A.read("../../data/test.npy")
	#A.write("../../data/test.npy", "../../data/check.su")
	
	

	



