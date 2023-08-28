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
		self.report()

	
	def readEBCDIC(self):
		''''function to read EBCDIC header'''
		with open(file=self._file, mode="rt", encoding="cp500") as f:
			f.seek(0)
			self.params["EBCDIC"] = f.read(3200)

	def writeEBCDIC(self, outfile, text=None):
		'''function to write EBCDIC header'''
		if text == None: text = self.params["EBCDIC"]
		if len(text) != 3200:
			raise ValueError("Text must be exactly 3200 characters long")
		with open(file=outfile, mode="wt", encoding="cp500") as f:
			f.write(text)

	def readBheader(self):
		'''function to read binary header'''
		_dtype=pack_dtype(values=segy_binary_header)
		with open(self._file, 'rb') as f:
			f.seek(3200)
			bheader = np.fromfile(f, dtype=_dtype, count=1)
			self.bheader = bheader
		self.params['bheader'] = {}
		for name in bheader.dtype.names:
			try:
				self.params['bheader'][name] = bheader[name][-1]
			except UnicodeDecodeError:
				pass #update this to not fail silently

	def writeBheader(self, outfile, bheader=None):
		'''function to write binary header
		   helper functions should be written 
		   which will update bheader based upon 
		   self.bheader'''
		
		if bheader == None: bheader = self.bheader
		_dtype=pack_dtype(values=segy_binary_header)
		
		# Ensure the dtype is big endian
		_dtype = _dtype.newbyteorder('>')
		bheader = bheader.astype(_dtype)

		with open(outfile, 'r+b') as f:  # 'r+b' to read and write in binary mode
			f.seek(3200)  # move to the start of the binary header
			bheader.tofile(f)


	def readNS(self):
		'''to do: add asserts'''
		ns = self.params["ns"] = self.params['bheader']['hns']
		
	def calculateChunks(self, fraction=2, offset=3600):	
		'''
		calculates chunk sizes for Segy files that are larger than RAM
		fraction: fraction of ram per chunk
		'''
		mem = memory()['free']
		print("free ram:", mem)
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
		for item in ["filesize", "tracesize", "ntraces", "nchunks", "chunksize", "ntperchunk", "remainder"]:
			if self.verbose:
				print(item, ": ", self.params[item])


	def read(self, overwrite=0):
		'''
		reads a Segy file to a .npy file in chunks. assumed IBM floats for now. extend for all data types
		
		'''
		self.calculateChunks()
		self.in_dtype = pack_dtype(values=segy_trace_header + [('trace', ('i4', self.params['ns']), 240)])
		self._dtype = pack_dtype(values=segy_trace_header + [('trace', (np.float32, self.params['ns']), 240)])
		self.outdata = np.memmap(filename=self._file+".npy", dtype=self._dtype, mode='w+', shape=self.params["ntraces"], order="F")
		
		nchunks = self.params["nchunks"]
		ntperchunk = self.params["ntperchunk"]
		remainder = self.params["remainder"]
		
		for i in range(nchunks):
			start_trace = i * ntperchunk
			end_trace = start_trace + ntperchunk
			chunk = np.fromfile(self._file, dtype=self.in_dtype, count=ntperchunk, offset=3600+(start_trace*self.params["tracesize"]))
			self.outdata[start_trace:end_trace] = chunk

	
		# process the remaining traces
		if remainder > 0:
			start_trace = nchunks * ntperchunk
			chunk = np.fromfile(self._file, dtype=self.in_dtype, count=remainder, offset=3600+(start_trace*self.params["tracesize"]))
			self.outdata[start_trace:] = chunk
		
		self.outdata.flush()
		self.outdata['trace'] = self.ibm2ieee(self.outdata['trace'].astype('i4'))

		return self.outdata

	def write(self, _infile, _outfile):
		"""
		Writes a Segy file from a .npy file.
		"""
		# Load .npy file
		self.out_dtype = pack_dtype(values=segy_trace_header + [('trace', ('>f4', self.params['ns']), 240)])
		data = np.memmap(filename=_infile, dtype=self.out_dtype, mode='r+', order="F")
		# Convert IEEE floats back to IBM floats
		# data['trace'] = self.ieee2ibm(data['trace'].astype('<i4'))
		self.writeEBCDIC(_outfile)
		self.writeBheader(_outfile)

		with open(_outfile, 'r+b') as segyfile:
			for trace in data:
				segyfile.write(trace.tobytes())

	def ibm2ieee(self, ibm):
		sign = ibm >> 31 & 0x01
		exponent = (ibm >> 24 & 0x7f)
		mantissa = (ibm & 0x00ffffff)
		mantissa = (mantissa * np.float32(1.0)) / pow(2.0, 24.0)
		ieee = (1.0 - 2.0 * sign) * mantissa * np.power(np.float32(16.0), exponent - 64.0)
		return ieee

	def ieee2ibm(self, ieee):
		ieee = ieee.astype(np.float32)
		expmask = 0x7f800000
		signmask = 0x80000000
		mantmask = 0x7fffff
		asint = ieee.view('i4')
		signbit = asint & signmask
		exponent = ((asint & expmask) >> 23) - 127
		# The IBM 7-bit exponent is to the base 16 and the mantissa is presumed to
		# be entirely to the right of the radix point. In contrast, the IEEE
		# exponent is to the base 2 and there is an assumed 1-bit to the left of the
		# radix point.
		exp16 = ((exponent+1) // 4)
		exp_remainder = (exponent+1) % 4
		exp16 += exp_remainder != 0
		downshift = np.where(exp_remainder, 4-exp_remainder, 0)
		ibm_exponent = np.clip(exp16 + 64, 0, 127)
		expbits = ibm_exponent << 24
		# Add the implicit initial 1-bit to the 23-bit IEEE mantissa to get the
		# 24-bit IBM mantissa. Downshift it by the remainder from the exponent's
		# division by 4. It is allowed to have up to 3 leading 0s.
		ibm_mantissa = ((asint & mantmask) | 0x800000) >> downshift
		# Special-case 0.0
		ibm_mantissa = np.where(ieee, ibm_mantissa, 0)
		expbits = np.where(ieee, expbits, 0)
		return signbit | expbits | ibm_mantissa


	def log(self, message):
		if self.verbose: print(message)

	def report(self):
		if self.verbose: pprint.pprint(self.params)
		