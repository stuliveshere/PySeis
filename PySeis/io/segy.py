import numpy as np
import os, sys
import pylab

segy_textual_header_dtype = np.dtype([('TFH', (np.str_,   80))])

segy_binary_header_dtype = np.dtype([
	('jobid', 'i4'),
	('lino', 'i4'),
	('reno', 'i4'),
	('ntrpr', 'i2'), # mandatory (prestack)
	('nart', 'i2'), # mandatory (prestack)
	('hdt', 'u2'), # mandatory (all)
	('dto', 'u2'),
	('hns', 'u2'), # mandatory (all)
	('nso', 'u2'),
	('format', 'i2'), # mandatory (all)
	('fold', 'i2'), # strongly recommended 
	('tsort', 'i2'), # strongly recommended 
	('vscode', 'i2'),
	('hsfs', 'i2'),
	('hsfe', 'i2'),
	('hslen', 'i2'),
	('hstyp', 'i2'),
	('schn', 'i2'),
	('hstas', 'i2'),
	('hstae', 'i2'),
	('htatyp', 'i2'),
	('hcorr', 'i2'),
	('bgrcv', 'i2'),
	('rcvm', 'i2'),
	('mfeet', 'i2'), # strongly recommended 
	('polyv', 'i2'),
	('vpol', 'i2'),
	('unassigned_1', (np.str_,   240)),
	('segyrev', 'i2'), # mandatory (all)
	('fixedlen', 'i2'), # mandatory (all)
	('numhdr', 'i2'), # mandatory (all)
	('unassigned_2', (np.str_,   94)),
])

segy_trace_header_dtype = np.dtype([
	('tracl',  'i4'), # strongly recommended 
	('tracr',  'i4'),
	('fldr',   'i4'), # strongly recommended 
	('tracf',  'i4'), # strongly recommended 
	('ep',     'i4'),
	('cdp',    'i4'),
	('cdpt',   'i4'),
	('trid',   'i2'), # strongly recommended 
	('nvs',    'i2'),
	('nhs',    'i2'),
	('duse',   'i2'),
	('offset', 'i4'),
	('gelev',  'i4'),
	('selev',  'i4'),
	('sdepth', 'i4'),
	('gdel',   'i4'),
	('sdel',   'i4'),
	('swdep',  'i4'),
	('gwdep',  'i4'),
	('scalel', 'i2'),
	('scalco', 'i2'),
	('sx',     'i4'),
	('sy',     'i4'),
	('gx',     'i4'),
	('gy',     'i4'),
	('counit', 'i2'),
	('wevel',   'i2'),
	('swevel',  'i2'),
	('sut',     'i2'),
	('gut',     'i2'),
	('sstat',   'i2'),
	('gstat',   'i2'),
	('tstat',   'i2'),
	('laga',    'i2'),
	('lagb',    'i2'),
	('delrt',   'i2'),
	('muts',    'i2'),
	('mute',    'i2'),
	('ns',      'i2'), # strongly recommended 
	('dt',      'i2'), # strongly recommended 
	('gain',    'i2'),
	('igc',    'i2'),
	('igi',    'i2'),
	('corr',   'i2'),
	('sfs',    'i2'),
	('sfe',    'i2'),
	('slen',   'i2'),
	('styp',   'i2'),
	('stas',   'i2'),
	('stae',   'i2'),
	('tatyp',  'i2'),
	('afilf',  'i2'),
	('afils',  'i2'),
	('nofilf', 'i2'),
	('nofils', 'i2'),
	('lcf',    'i2'),
	('hcf',    'i2'),
	('lcs',    'i2'),
	('hcs',    'i2'),
	('year',   'i2'),
	('day',    'i2'),
	('hour',   'i2'),
	('minute', 'i2'),
	('sec',    'i2'),
	('timbas', 'i2'),
	('trwf',   'i2'),
	('grnors', 'i2'),
	('grnofr', 'i2'),
	('grnlof', 'i2'),
	('gaps',   'i2'),
	('otrav',  'i2'),
	('cdpx',   'i4'),
	('cdpy',   'i4'),
	('iline',  'i4'),
	('xline',  'i4'),
	('shnum',  'i4'),
	('shsca',  'i2'),
	('tval',   'i2'),
	('tconst4', 'i4'),
	('tconst2', 'i2'),
	('tunits', 'i2'),
	('device', 'i2'),
	('tscalar', 'i2'),
	('stype',  'i2'),
	('sendir', 'i4'),
	('unknown', 'i2'),
	('smeas4', 'i4'),
	('smeas2', 'i2'),
	('smeasu', 'i2'),
	('unass1', 'i4'),
	('unass2', 'i4'),
	])

def read_EBCDIC(_file):
	''''function to read EBCDIC header'''
	with open(_file, 'rb') as f:
		header = np.fromfile(f, dtype='u2', count=3200/2)
		if np.any(np.diff(header)): #check for content
			f.seek(0)
			return f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
		else:
			return None

def read_bheader(_file):
	''''function to read binary header'''
	with open(_file, 'rb') as f:
		f.seek(3200)
		binary = np.fromstring(f.read(400), dtype=segy_binary_header_dtype)
		#endian sanity checks. this is pretty crude and will need revisting.
		try:
			assert 0 < binary['format'] < 9
		except AssertionError:
			binary = binary.byteswap()
		return binary

def num_traces(_file, ns):
	with open(_file, 'rb') as f:
		f.seek(0, os.SEEK_END)
		size = f.tell()
		nt = (size-3600.0)/(240.0+ns*4.0)
		assert nt % 1 == 0
	return nt
	
def read_traces(_file, ns, chunksize=0.01): 
	#assuming ibm floats for now
	#chunksize in Gb
	ibmtype = np.dtype(segy_trace_header_dtype.descr + [('data', ('<i4',ns))])
	ftype = np.dtype(segy_trace_header_dtype.descr + [('data', ('<f4',ns))])
	with open(_file, 'rb') as f:
		#some trickery to calculate filesize
		f.seek(0, os.SEEK_END)
		filesize = f.tell() #filesize in bytes
		#caculate size of traces
		tracesize = 240+ns*4.0
		ntraces = (filesize-3600)/tracesize
		
		chunks = min(filesize, np.floor(filesize/(chunksize*1.0e9)))
		tracesPerChunk = min(ntraces, np.floor(chunksize*1.0e9/tracesize))
		chunksize = tracesPerChunk*tracesize
		remainder = divmod(filesize-3600, chunksize)
		
			
		
		
		f.seek(3600)    #start at end of binary header block
		for n in range(int(chunks+1)):
			if n ==int(chunks+1): chunksize = remainder #last chunk
			data = np.fromfile(f, dtype=ftype, count=int(chunksize))
			data['data'] = ibm2ieee(data['data'].astype(np.int32))
			yield data

def ibm2ieee(ibm):
	s = ibm >> 31 & 0x01 
	exp = ibm >> 24 & 0x7f 
	fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
	ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
	return ieee
		
		
def read(_file):
	EBCDIC = read_EBCDIC(_file)
	bh = read_bheader(_file)
	assert np.any(np.diff(bh['hns'][:])) == False #check ns is constant
	assert np.any(np.diff(bh['hdt'][:])) == False #check ns is constant
	ns = bh['hns'][0]
	dt = bh['dto'][0]
	print ns, dt
	for i in read_traces(_file, ns):
		i['data'][i['data'] > 1e10] = 0
		pylab.plot(i[10]['data'])
		pylab.show()

if __name__ == "__main__":
	file = "../../data/sample.sgy"
	read(file)