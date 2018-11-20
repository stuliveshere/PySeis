#!/usr/bin/python -d
'''
python SU stdin/stdout interface module

	data = readSU()
	writeSU(data)
	
uses custom dtypes for a very fast read/write to stdin/stdout
returns a single np.ndarray with dtype=sufile
a numpy 2d array of traces can be addressed as data['traces']
each header term can also be addressed via data['insertheaderterm']
'''

import numpy as np, sys, os, os.path
from headers import su_header_dtype
import logging

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

def readInChunks(_file, _dtype):
	pass
	




	
def readSUheader(filename):
	raw = open(filename, 'rb').read()
	return np.fromstring(raw, dtype=su_header_dtype, count=1)

def readSU(filename=None):
	if filename == None:
		raw= sys.stdin.read()
	else:
		raw = open(filename, 'rb').read()
	su_header = np.fromstring(raw, dtype=su_header_dtype, count=1)
	ns = su_header['ns'][0]
	file_dtype = typeSU(ns)
	data = np.fromstring(raw, dtype=file_dtype)
	return data
	
def writeSU(data, filename=None):
	if filename == None:
		data.tofile(sys.stdout)
	else:
		data.tofile(filename)
		
class SU(object):
	'''
	To do:
		test for endianness by checking for sane values, store in flag
	'''
	def __init__(self, _file):
		self._file = _file
		self.params = {}
		raw = open(_file, 'rb').read(240)
		self.ns = np.fromstring(raw, dtype=su_header_dtype, count=1).byteswap()['ns'] 
		self._dtype = np.dtype(su_header_dtype.descr + [('trace', ('<f4',self.ns))])
		self.calculateChunks()

		
	def calculateChunks(self):	
		mem = memory()['free']
		log.debug("Current free memory: %d bytes" %mem)
		with open(self._file, 'rb') as f:
			f.seek(0, os.SEEK_END)
			filesize = f.tell() #filesize in bytes
			log.debug("filesize:%d bytes" %filesize)
			chunks = np.ceil(filesize/(mem)) #number of chunks
			log.debug("number of chunks: %d" %chunks)
			chunksize, remainder = divmod(filesize, chunks)
			log.debug("chunksize: %d \n remaining bytes: %d" %(chunksize, remainder))
			tracesize = 240+self.ns*4.0
			log.debug("trace size: %d" %tracesize)
			nTracesPerChunk = chunksize/tracesize
			assert chunksize%tracesize == 0
			

	
			
		
		
		
if __name__ == "__main__":
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
	log = logging.getLogger()
	A = SU("../../data/big.su")
	
	

	



