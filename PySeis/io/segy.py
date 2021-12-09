import numpy as np
import os, sys
from .su import memory
import pprint
from textwrap import wrap
#overwrite these header definitions for custom headers
from .headers import segy_trace_header_dtype, segy_binary_header_dtype, segy_trace_header_repack
import numpy.lib.recfunctions as rf 


class Segy(object):
	'''
	reading and writing segy files, including those larger than RAM,
	to and from .npy files
	'''
	def __init__(self, _file, verbose=0):
		self.params = {}
		self.verbose = verbose
		self._file = self.params['filename'] = _file
		self.readEBCDIC()
		self.readBheader()
		self.readNS()
		self.calculateChunks()
		self.report()

	
	def readEBCDIC(self):
		''''function to read EBCDIC header'''
		with open(self._file, "rt", "cp500") as f:
			f.seek(0)
			self.params["EBCDIC"] = wrap(str(f.read(3200), 80)

	def readBheader(self):
		'''function to read binary header'''

		with open(self._file, 'rb') as f:
			f.seek(3200)
			bheader = np.fromfile(f, dtype=segy_binary_header_dtype, count=1)
			#endian sanity checks. this is pretty crude and will need revisting.
			try:
				assert 0 < bheader['format'] < 9
			except AssertionError:
				bheader = bheader.byteswap()
		self.params['bheader'] = {}
		for name in bheader.dtype.names:
			try:
				self.params['bheader'][name] = bheader[name][-1]
			except UnicodeDecodeError:
				pass

	def readNS(self):
		'''to do: add asserts'''
		ns = self.params["ns"] = self.params['bheader']['hns']
		_dtype = segy_trace_header_repack([('trace', ('<f4', ns), 240)])
		self._dtype=rf.repack_fields(_dtype)
		
	def calculateChunks(self, fraction=2, offset=3600):	
		'''
		calculates chunk sizes for Segy files that are larger than RAM
		'''
		mem = memory()['free']
		with open(self._file, 'rb') as f:
			f.seek(0, os.SEEK_END)
			self.params["filesize"] = filesize = f.tell()-offset #filesize in bytes
			self.params["tracesize"] = tracesize = 240+(self.params["ns"]*4)
			self.params["ntraces"] = ntraces = int(filesize/tracesize)
			self.params["nchunks"] = nchunks = int(np.ceil(filesize/(mem*fraction))) #number of chunks
			self.params["chunksize"] = chunksize = int((filesize/nchunks) - (filesize/nchunks)%tracesize)
			self.params["ntperchunk"] = int(chunksize/tracesize)
			self.params["remainder"] = remainder = filesize - chunksize*nchunks
			assert filesize%tracesize == 0
			assert chunksize%tracesize == 0

	def report(self):
		if self.verbose: pprint.pprint(self.params)
		
		
	def read(self, _file, overwrite=0):
		'''
		reads a Segy file to a .npy file. assumed IBM floats fot now. extend for all data types
		'''
		if (overwrite==0 and os.path.isfile(_file)): return
		self.outdata = np.lib.format.open_memmap(_file, mode='w+', dtype=self._dtype, shape=self.params["ntraces"])
		with open(self._file, 'rb') as f:
			f.seek(3600)
			for i in range(self.params["nchunks"]):
				start = i*self.params["ntperchunk"]
				end = (i+1)*self.params["ntperchunk"]
				chunk = np.fromstring(f.read(self.params["chunksize"]), dtype=self._dtype)
				chunk['trace'] = self.ibm2ieee(chunk['trace'].astype('<i4'))
				self.outdata[start:end] = chunk
				self.outdata.flush()
			remainder = np.fromstring(f.read(self.params["remainder"]), dtype=self._dtype)
			remainder['trace'] = self.ibm2ieee(remainder['trace'].astype('<i4'))
			self.outdata[end:] = remainder
			self.outdata.flush()
	
	def write(self, _infile, _outfile):
		'''
		writes a .npy file to a segy file
		'''
		#npyFile = np.memmap(_infile, dtype=self._dtype, mode='r')
		#npyFile.tofile(_outfile)
		pass
		
	def ibm2ieee(self, ibm):
		s = ibm >> 31 & 0x01 
		exp = ibm >> 24 & 0x7f 
		fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
		ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
		return ieee

	def log(self, message):
		if self.verbose: print(message)

if __name__ == "__main__":
	file = "../../data/sample.sgy"
	A = Segy(file)
	A.read("../../data/sample.npy")