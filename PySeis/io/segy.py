import numpy as np
import os, sys
import pprint
#overwrite these header definitions for custom headers
from .tools import pack_dtype, memory
from .headers import segy_binary_header, segy_trace_header
from numpy.lib.format import open_memmap
import dask, dask.array as da


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
		with open(file=self._file, mode="rt", encoding="cp500") as f:
			f.seek(0)
			self.params["EBCDIC"] = f.read(3200)

	def readBheader(self):
		'''function to read binary header'''
		_dtype=pack_dtype(values=segy_binary_header)

		with open(self._file, 'rb') as f:
			f.seek(3200)
			bheader = np.fromfile(f, dtype=_dtype, count=1)
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
		self._dtype = pack_dtype(values=segy_trace_header + [('trace', ('<f4', ns), 240)])

		
	def calculateChunks(self, fraction=2, offset=3600):	
		'''
		calculates chunk sizes for Segy files that are larger than RAM
		fraction: fraction of ram per chunk
		'''
		mem = memory()['free']
		with open(self._file, 'rb') as f:
			f.seek(0, os.SEEK_END)
			self.params["filesize"] = filesize = f.tell()-offset #filesize in bytes, minus headers
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
		reads a Segy file to a .npy file. assumed IBM floats for now. extend for all data types
		'''
		self.outdata =np.memmap(filename=_file, dtype=self._dtype, mode='w+', shape=self.params["ntraces"], order="F")
		for i in range(self.params["ntraces"]):
			chunk = np.fromfile(self._file, dtype=self._dtype, count=1, offset=3600+(i*self.params["tracesize"])).byteswap()
			#chunk['trace'] = self.ibm2ieee(chunk['trace'].astype('<i4'))
			self.outdata[i] = chunk
		self.outdata.flush()
		data = np.memmap(filename=_file, dtype=self._dtype, mode='r+', shape=self.params["ntraces"], order="F")
		a = da.from_array(data)
		data['trace'] = self.ibm2ieee(a['trace'].astype('<i4'))
		data.flush()

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

