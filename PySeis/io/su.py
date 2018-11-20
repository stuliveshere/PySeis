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
	

def calculateChunks(_file, _dtype):	
	mem = memory()['free']
	with open(_file, 'rb') as f:
		f.seek(0, os.SEEK_END)
		filesize = f.tell() #filesize in bytes
		#caculate size of traces
		tracesize = 240+ns*4.0
		chunks = np.ceil(filesize/(mem/4.0))
		print chunks

def typeSU(ns):
	return np.dtype(su_header_dtype.descr + [('trace', ('<f4',ns))])
	
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
		
if __name__ == "__main__":
	data = readSU(filename="../../data/sample.su")
	
	

	



