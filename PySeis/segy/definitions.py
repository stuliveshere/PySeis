import numpy as np
import string
import sys
import struct
import tables as tb
import math
import os
import re

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())

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




keylist = 	segy_textual_header_dtype.names + \
		segy_binary_header_dtype.names + \
		segy_trace_header_dtype.names 
		


class segy:
	def __init__(self, database, **kwargs):
		#~ if not set(kwargs.keys()).issubset(keylist):
			#~ raise Exception("Invalid key in segy kwargs")
		#~ if not filename: 
			#~ self.initialiseFramework()
		#~ else:
			#~ self.loadFramework()
		
		self.db=database	
		
		
		
	def initialiseFramework(self):
		
		
		pass
		#initialise text header
		
		#initialise binary header
	
	def loadFramework(self):
		pass
		#pull a few key items in from segy file
		
	def load(self, filelist, headers_only=False):
		'''
		imports a segy file to pytable.
		note format header entry -must- be
		set correctly for this to work
		'''
		
			
		for filename in filelist:
			file = filename.strip()
			#group name, ie line name, from file name
			group = file.split('/')[-1].split('.')[0]
			group = group.translate(None, delchars)
			#create a h5 node
			node = self.db.createGroup("/", group, 'PySeis Node')

			with open(file, 'rb') as f:
				print file
				#create EBCDC tab3e
				fh = self.db.createTable(node, 'FH', segy_textual_header_dtype, "EBCDIC File Header")
				#import EBCDC
				EBCDC = f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
				fh.append(np.fromstring(EBCDC, dtype=segy_textual_header_dtype))
				
				#import binary header
				bh = self.db.createTable(node, 'BH', segy_binary_header_dtype, "Binary File Header")
				binary = np.fromstring(f.read(400), dtype=segy_binary_header_dtype)
				#endian sanity checks. this is pretty crude and will need revisting.

				try:
					assert 0 < binary['format'] < 9
				except AssertionError:
					binary = binary.byteswap()

				assert 0 < binary['format'] < 9				
				bh.append(binary)
				
				#insert file size sanity checks and create file map table
				#file map table calculates the byte location of each item in the file
				#to be used for overwrites/header_only cases
					
				#create tables for trace headers and traces
				th = self.db.createTable(node, 'TH', segy_trace_header_dtype, "Trace Header")
				td = self.db.create_earray(node,
							name = 'TD',
							atom = tb.Float32Atom(), 
							shape = (0,binary['hns']),
							title = "Trace Header", 
							filters = tb.Filters(complevel=6, complib='zlib'),
							expectedrows=100000)
							
				#read in trace headers and traces
				counts = 1e5
				header_array = np.zeros(counts, dtype=segy_trace_header_dtype)
				if not headers_only: data_array = np.zeros(counts, dtype=('f4',binary['hns']))
				counter = 0
				for chunk in iter(lambda: f.read(240), ""):
					header = np.fromstring(chunk, dtype=segy_trace_header_dtype).byteswap()

					try:
						assert header['ns'] == binary['hns'] 
					except AssertionError:
						header = header.newbyteorder('S')
					try:
						assert header['ns'] == binary['hns'] 
					except AssertionError:
						print header['ns'], binary['hns'] , binary['format']
						header = header.newbyteorder('S')
						print header['ns'], binary['hns'] , binary['format']
						print f.tell()
						
					assert header['ns'] == binary['hns']   


					if not headers_only:
						if binary['format'] == 1:
							data = self.ibm2ieee(np.fromfile(f, dtype='>i4', count=header['ns'])).reshape(1,header['ns'])
						elif binary['format'] == 5:
							data = np.fromfile(f, dtype='>f4', count=header['ns']).reshape(1,header['ns'])
					else:
						f.seek(header['ns']*4, 1)
						
					header_array[counter] = header	
					if not headers_only: data_array[counter] = data
					counter += 1
					if counter == 1e5: 
						th.append(header_array.byteswap())
						if not headers_only: td.append(data_array)
						counter = 0					
					
				th.append(header_array[:counter].byteswap())
				if not headers_only: td.append(data_array[:counter])

		
		
	def exportFIle(self, filename):
		pass
	
	def ibm2ieee(self, ibm): 
	    s = ibm >> 31 & 0x01 
	    exp = ibm >> 24 & 0x7f 
	    fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
	    ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
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
	    

 
# convert floating point to ibm
	def ieee2ibm2(x, endian):
	# check input data
		if(x > 7.236998675585915e+75): return(0x7ffffff0)
		if(x < -7.236998675585915e+75): return(0xfffffff0)
		if(x == 0): return 0
		if(x == np.NAN):  return (0x7fffffff) #check input if NAN number
		
		#conversion log2 from matlab
		F, E = math.frexp(abs(x))

		e = float (E/4.0);              # exponent of base 16
		ec = math.ceil(e);            # adjust upwards to integer
		p = ec + 64;                  # offset exponent

		f = F * pow(2,(-4*(ec-e)));   #  correct mantissa for fractional part of exponent
		# convert to integer. Roundoff here can be as large as
		# 0.5/2^20 when mantissa is close to 1/16 so that
		# 3 bits of signifance are lost.
		f1 = round(f * 0x1000000);

		# format hex
		# put exponent in first byte of psi.
		tmpi = p * 0x1000000;
		if(tmpi<=0):
			psi = 0
		elif(tmpi>=0xFFFFFFFF):
			psi = 0xFFFFFFFF
		else:
			psi = tmpi

		# put mantissa into last 3 bytes of phi
		if(f1<=0):
			phi = 0
		elif(f1>=0xFFFFFFFF):
			phi = 0xFFFFFFFF
		else:
			phi = f1

		# make bit representation
		# exponent and mantissa
		b = int(psi) | int(phi)
		# sign bit
		if(x<0):
			b = b + 0x80000000

		#print b
		b = np.uint32(b)
		if(endian):      #big endian
			cval = struct.pack(">i",b)
		else:            #litte endian
			cval = struct.pack("<i",b)

		return (cval)

		
if __name__ == '__main__':
	os.chdir('../../data/')
	filelist = [a for a in os.listdir('.') if '.sgy' in a]
	db = tb.openFile('test.h5', mode = "w", title='test')
	
	a = segy(db)
	a.load(filelist, headers_only=True)
	
