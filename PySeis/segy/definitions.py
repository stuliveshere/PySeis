import numpy as np

segy_textual_header_dtype = np.dtype([('TFH', (np.str_,   3200))])

segy_binary_header_dtype = np.dtype([
    ('jobid', '>i4'),
    ('lino', '>i4'),
    ('reno', '>i4'),
    ('ntrpr', '>i2'), # mandatory (prestack)
    ('nart', '>i2'), # mandatory (prestack)
    ('hdt', '>u2'), # mandatory (all)
    ('dto', '>u2'),
    ('hns', '>u2'), # mandatory (all)
    ('nso', '>u2'),
    ('format', '>i2'), # mandatory (all)
    ('fold', '>i2'), # strongly recommended 
    ('tsort', '>i2'), # strongly recommended 
    ('vscode', '>i2'),
    ('hsfs', '>i2'),
    ('hsfe', '>i2'),
    ('hslen', '>i2'),
    ('hstyp', '>i2'),
    ('schn', '>i2'),
    ('hstas', '>i2'),
    ('hstae', '>i2'),
    ('htatyp', '>i2'),
    ('hcorr', '>i2'),
    ('bgrcv', '>i2'),
    ('rcvm', '>i2'),
    ('mfeet', '>i2'), # strongly recommended 
    ('polyv', '>i2'),
    ('vpol', '>i2'),
    ('unassigned_1', (np.str_,   240)),
    ('segyrev', '>i2'), # mandatory (all)
    ('fixedlen', '>i2'), # mandatory (all)
    ('numhdr', '>i2'), # mandatory (all)
    ('unassigned_2', (np.str_,   94)),
])

segy_trace_header_dtype = np.dtype([
    ('tracl',  '>i4'), # strongly recommended 
    ('tracr',  '>i4'),
    ('fldr',   '>i4'), # strongly recommended 
    ('tracf',  '>i4'), # strongly recommended 
    ('ep',     '>i4'),
    ('cdp',    '>i4'),
    ('cdpt',   '>i4'),
    ('trid',   '>i2'), # strongly recommended 
    ('nvs',    '>i2'),
    ('nhs',    '>i2'),
    ('duse',   '>i2'),
    ('offset', '>i4'),
    ('gelev',  '>i4'),
    ('selev',  '>i4'),
    ('sdepth', '>i4'),
    ('gdel',   '>i4'),
    ('sdel',   '>i4'),
    ('swdep',  '>i4'),
    ('gwdep',  '>i4'),
    ('scalel', '>i2'),
    ('scalco', '>i2'),
    ('sx',     '>i4'),
    ('sy',     '>i4'),
    ('gx',     '>i4'),
    ('gy',     '>i4'),
    ('counit', '>i2'),
    ('wevel',   '>i2'),
    ('swevel',  '>i2'),
    ('sut',     '>i2'),
    ('gut',     '>i2'),
    ('sstat',   '>i2'),
    ('gstat',   '>i2'),
    ('tstat',   '>i2'),
    ('laga',    '>i2'),
    ('lagb',    '>i2'),
    ('delrt',   '>i2'),
    ('muts',    '>i2'),
    ('mute',    '>i2'),
    ('ns',      '>i2'), # strongly recommended 
    ('dt',      '>i2'), # strongly recommended 
    ('gain',    '>i2'),
    ('igc',    '>i2'),
    ('igi',    '>i2'),
    ('corr',   '>i2'),
    ('sfs',    '>i2'),
    ('sfe',    '>i2'),
    ('slen',   '>i2'),
    ('styp',   '>i2'),
    ('stas',   '>i2'),
    ('stae',   '>i2'),
    ('tatyp',  '>i2'),
    ('afilf',  '>i2'),
    ('afils',  '>i2'),
    ('nofilf', '>i2'),
    ('nofils', '>i2'),
    ('lcf',    '>i2'),
    ('hcf',    '>i2'),
    ('lcs',    '>i2'),
    ('hcs',    '>i2'),
    ('year',   '>i2'),
    ('day',    '>i2'),
    ('hour',   '>i2'),
    ('minute', '>i2'),
    ('sec',    '>i2'),
    ('timbas', '>i2'),
    ('trwf',   '>i2'),
    ('grnors', '>i2'),
    ('grnofr', '>i2'),
    ('grnlof', '>i2'),
    ('gaps',   '>i2'),
    ('otrav',  '>i2'),
    ('cdpx',   '>i4'),
    ('cdpy',   '>i4'),
    ('iline',  '>i4'),
    ('xline',  '>i4'),
    ('shnum',  '>i4'),
    ('shsca',  '>i2'),
    ('tval',   '>i2'),
    ('tconst4', '>i4'),
    ('tconst2', '>i2'),
    ('tunits', '>i2'),
    ('device', '>i2'),
    ('tscalar', '>i2'),
    ('stype',  '>i2'),
    ('sendir', '>i4'),
    ('unknown', '>i2'),
    ('smeas4', '>i4'),
    ('smeas2', '>i2'),
    ('smeasu', '>i2'),
    ('unass1', '>i4'),
    ('unass2', '>i4'),
    ])


#note the mandatory header is little endian... it is not directly coupled to file IO
segy_mandatory_header_dtype = np.dtype([
    ('ntrpr', 'i2'), # number of data traces per record
    ('nart', 'i2'), # number of auxiliary traces per record
    ('hdt', 'u2'), # sample interval in microsecs for this reel
    ('hns', 'u2'), #  number of samples per trace for this reel
    ('format', 'i2'), # 1 = 4-byte IBM floating-point, 5 = 4-byte IEEE floating-point
    ('fold', 'i2'), # CDP fold expected per CDP ensemble
    ('tsort', 'i2'), # trace sorting code: 1 = As recorded (no sorting) 5 = Common source point
    ('mfeet', 'i2'), # strongly recommended measurement system code = 1
    ('segyrev', 'i2'), # 0x0100
    ('fixedlen', 'i2'), # A value of one indicates that all traces in this SEG Y file are guaranteed to have the same sample interval 
    ('numhdr', 'i2'), # Number Extended Textual File Header records following 
  ])  

keylist = 	segy_textual_header_dtype.names + \
		segy_binary_header_dtype.names + \
		segy_trace_header_dtype.names 
		


class segy:
	def __init__(self, database, filename=None, **kwargs):
		if not set(kwargs.keys()).issubset(keylist):
			raise Exception("Invalid key in segy kwargs")
		if not filename: 
			self.initialiseFramework()
		else:
			self.loadFramework()
			
	def initialiseFramework(self):
		
		
		pass
		#initialise text header
		
		#initialise binary header
	
	def loadFramework(self):
		pass
		#pull a few key items in from segy file
		
	def importFIle(self, h5):
		pass
		
	def exportFIle(self, filename):
		pass
	
	def ibm2ieee(ibm): 
	    s = ibm >> 31 & 0x01 
	    exp = ibm >> 24 & 0x7f 
	    fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
	    ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
	    return ieee 

	def ieee2ibm(ieee): 
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

		
if __name__ == '__main__':
	a = segy()
	
