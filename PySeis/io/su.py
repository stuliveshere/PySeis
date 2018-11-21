'''
'''

import numpy as np, sys, os
import mmap
from headers import su_header_dtype


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
	To do:
		test for endianness by checking for sane values, store in flag
	'''
	def __init__(self, _file):
		self._file = _file
		self.params = {}
		raw = open(_file, 'rb').read(240)
		self.params["ns"] = self.ns = np.fromstring(raw, dtype=su_header_dtype, count=1).byteswap()['ns'] 
		self._dtype = np.dtype(su_header_dtype.descr + [('trace', ('<f4',self.ns))])
		self.calculateChunks()

		
	def calculateChunks(self, fraction=2):	
		mem = memory()['free']
		with open(self._file, 'rb') as f:
			f.seek(0, os.SEEK_END)
			self.params["filesize"] = filesize = f.tell() #filesize in bytes
			self.params["tracesize"] = tracesize = 240+self.ns*4.0
			self.params["ntraces"] = ntraces = int(filesize/tracesize)
			self.params["nchunks"] = nchunks = int(np.ceil(filesize/(mem*fraction))) #number of chunks
			self.params["chunksize"] = chunksize = (filesize/nchunks) - (filesize/nchunks)%tracesize
			self.params["ntperchunk"] = int(chunksize/tracesize)
			self.params["remainder"] = remainder = filesize - chunksize*nchunks
			assert filesize%tracesize == 0
			assert chunksize%tracesize == 0
			
	
	def write(self, _file):
		#self.outdata = np.lib.format.open_memmap(_file, dtype=self._dtype, shape=self.params["ntraces"], mode='w+')
		self.outdata = np.memmap(_file, mode='w+', dtype=self._dtype, shape=self.params["ntraces"])
 		with open(self._file, 'rb') as f:
			f.seek(0)
			for i in range(self.params["nchunks"]):
				start = i*self.params["ntperchunk"]
				end = (i+1)*self.params["ntperchunk"]
				self.outdata[start:end] = np.fromstring(f.read(self.params["chunksize"]), dtype=self._dtype)
				self.outdata.flush()
			self.outdata[end:] = np.fromstring(f.read(self.params["remainder"]), dtype=self._dtype)
 			self.outdata.flush()
	
	def check(self, _infile, _outfile):
		npyFile = np.memmap(_infile, dtype=self._dtype, mode='r')
		npyFile.tofile(_outfile)

if __name__ == "__main__":
	#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
	#log = logging.getLogger()
	A = SU("../../data/big.su")
	#A.write("../../data/test.npy")
	A.check("../../data/test.npy", "../../data/check.su")
	
	

	



