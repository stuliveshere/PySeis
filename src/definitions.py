import tables as tb
import numpy as np

class SU_header(tb.IsDescription):
	tracl =  tb.Int32Col()	
	tracr =  tb.Int32Col()
	fldr =  tb.Int32Col()
	tracf =  tb.Int32Col()
	ep =  tb.Int32Col()
	cdp =  tb.Int32Col()
	cdpt =  tb.Int32Col()
	trid =  tb.Int16Col()
	nvs =  tb.Int16Col()
	nhs =  tb.Int16Col()
	duse =  tb.Int16Col()
	offset =  tb.Int32Col()
	gelev =  tb.Int32Col()
	selev =  tb.Int32Col()
	sdepth =  tb.Int32Col()
	gdel =  tb.Int32Col()
	sdel =  tb.Int32Col()
	swdep =  tb.Int32Col()
	gwdep =  tb.Int32Col()
	scalel =  tb.Int16Col()
	scalco =  tb.Int16Col()
	sx =  tb.Int32Col()
	sy =  tb.Int32Col()
	gx =  tb.Int32Col()
	gy =  tb.Int32Col()
	counit =  tb.Int16Col()
	wevel =  tb.Int16Col()
	swevel =  tb.Int16Col()
	sut =  tb.Int16Col()
	gut =  tb.Int16Col()
	sstat =  tb.Int16Col()
	gstat =  tb.Int16Col()
	tstat =  tb.Int16Col()
	laga =  tb.Int16Col()
	lagb =  tb.Int16Col()
	delrt =  tb.Int16Col()
	muts =  tb.Int16Col()
	mute =  tb.Int16Col()
	ns =  tb.UInt16Col() 
	dt =  tb.UInt16Col() 
	gain =  tb.Int16Col()
	igc =  tb.Int16Col()
	igi =  tb.Int16Col()
	corr =  tb.Int16Col()
	sfs =  tb.Int16Col()
	sfe =  tb.Int16Col()
	slen =  tb.Int16Col()
	styp =  tb.Int16Col()
	stas =  tb.Int16Col()
	stae =  tb.Int16Col()
	tatyp =  tb.Int16Col()
	afilf =  tb.Int16Col()
	afils =  tb.Int16Col()
	nofilf =  tb.Int16Col()
	nofils =  tb.Int16Col()
	lcf =  tb.Int16Col()
	hcf =  tb.Int16Col()
	lcs =  tb.Int16Col()
	hcs =  tb.Int16Col()
	year =  tb.Int16Col()
	day =  tb.Int16Col()
	hour =  tb.Int16Col()
	minute =  tb.Int16Col()
	sec =  tb.Int16Col()
	timebas =  tb.Int16Col()
	trwf =  tb.Int16Col()
	grnors =  tb.Int16Col()
	grnofr =  tb.Int16Col()
	grnlof =  tb.Int16Col()
	gaps =  tb.Int16Col()
	otrav =  tb.Int16Col() 
	d1 = tb.Float32Col() 
	f1 = tb.Float32Col() 
	d2 = tb.Float32Col() 
	f2 = tb.Float32Col() 
	ShotPoint =  tb.Int32Col() 
	unscale =  tb.Int16Col() 
	TraceValueMeasurementUnit =  tb.Int16Col()
	TransductionConstantMantissa =  tb.Int32Col()
	TransductionConstantPower =  tb.Int16Col()
	TransductionUnit =  tb.Int16Col()
	TraceIdentifier =  tb.Int16Col()
	ScalarTraceHeader =  tb.Int16Col()
	SourceType =  tb.Int16Col()
	SourceEnergyDirectionMantissa =  tb.Int32Col()
	SourceEnergyDirectionExponent =  tb.Int16Col()
	SourceMeasurementMantissa =  tb.Int32Col()
	SourceMeasurementExponent =  tb.Int16Col()
	SourceMeasurementUnit =  tb.Int16Col()
	UnassignedInt1 =  tb.Int32Col()
	ns1 =  tb.Int32Col()
	
su_header_dtype = np.dtype([
('tracl', np.int32),
('tracr', np.int32),
('fldr', np.int32),
('tracf', np.int32),
('ep', np.int32),
('cdp', np.int32),
('cdpt', np.int32),
('trid', np.int16),
('nvs', np.int16),
('nhs', np.int16),
('duse', np.int16),
('offset', np.int32),
('gelev', np.int32),
('selev', np.int32),
('sdepth', np.int32),
('gdel', np.int32),
('sdel', np.int32),
('swdep', np.int32),
('gwdep', np.int32),
('scalel', np.int16),
('scalco', np.int16),
('sx', np.int32),
('sy', np.int32),
('gx', np.int32),
('gy', np.int32),
('counit', np.int16),
('wevel', np.int16),
('swevel', np.int16),
('sut', np.int16),
('gut', np.int16),
('sstat', np.int16),
('gstat', np.int16),
('tstat', np.int16),
('laga', np.int16),
('lagb', np.int16),
('delrt', np.int16),
('muts', np.int16),
('mute', np.int16),
('ns', np.uint16),
('dt', np.uint16),
('gain', np.int16),
('igc', np.int16),
('igi', np.int16),
('corr', np.int16),
('sfs', np.int16),
('sfe', np.int16),
('slen', np.int16),
('styp', np.int16),
('stas', np.int16),
('stae', np.int16),
('tatyp', np.int16),
('afilf', np.int16),
('afils', np.int16),
('nofilf', np.int16),
('nofils', np.int16),
('lcf', np.int16),
('hcf', np.int16),
('lcs', np.int16),
('hcs', np.int16),
('year', np.int16),
('day', np.int16),
('hour', np.int16),
('minute', np.int16),
('sec', np.int16),
('timebas', np.int16),
('trwf', np.int16),
('grnors', np.int16),
('grnofr', np.int16),
('grnlof', np.int16),
('gaps', np.int16),
('otrav', np.int16), #179,180
('d1', np.float32), #181,184
('f1', np.float32), #185,188
('d2', np.float32), #189,192
('f2', np.float32), #193, 196
('ShotPoint', np.int32), #197,200
('unscale', np.int16), #201, 204
('TraceValueMeasurementUnit', np.int16),
('TransductionConstantMantissa', np.int32),
('TransductionConstantPower', np.int16),
('TransductionUnit', np.int16),
('TraceIdentifier', np.int16),
('ScalarTraceHeader', np.int16),
('SourceType', np.int16),
('SourceEnergyDirectionMantissa', np.int32),
('SourceEnergyDirectionExponent', np.int16),
('SourceMeasurementMantissa', np.int32),
('SourceMeasurementExponent', np.int16),
('SourceMeasurementUnit', np.int16),
('UnassignedInt1', np.int32),
('ns1', np.int32),
])


segy_trace_header_dtype = np.dtype([
    {"tracl",  4},  

    {"tracr",  4},  

    {"fldr",   4},  

    {"tracf",  4},  

    {"ep",     4},  

    {"cdp",    4},  

    {"cdpt",   4},  

    {"trid",   2},  /* trace identification code:
                        1 = seismic data
                        2 = dead
                        3 = dummy
                        4 = time break
                        5 = uphole
                        6 = sweep
                        7 = timing
                        8 = water break
                        9---, N = optional use (N = 32,767) 28 */

    {"nvs",    2},  /* number of vertically summed traces (see
		    vscode in bhed structure) 30 */

    {"nhs",    2},  /* number of horizontally summed traces (see
		    vscode in bhed structure) 32 */

    {"duse",   2},  /* data use:
		    1 = production
		    2 = test 34 */

    {"offset", 4},  /* distance from source point to receiver
		    group (negative if opposite to direction
		    in which the line was shot) 36 */

    {"gelev",  4},  /* receiver group elevation from sea level
		    (above sea level is positive) 40 */

    {"selev",  4},  /* source elevation from sea level
		     (above sea level is positive) 44 */

    {"sdepth", 4},  

    {"gdel",   4},  

    {"sdel",   4},  

    {"swdep",  4},  

    {"gwdep",  4},  

    {"scalel", 2},  /* scale factor for previous 7 entries
		     with value plus or minus 10 to the
		     power 0, 1, 2, 3, or 4 (if positive,
		     multiply, if negative divide) 68 */

    {"scalco", 2},  /* scale factor for next 4 entries
		     with value plus or minus 10 to the
		     power 0, 1, 2, 3, or 4 (if positive,
		     multiply, if negative divide) 70 */

    {"sx",     4},  

    {"sy",     4},  

    {"gx",     4},  

    {"gy",     4},  

    {"counit", 2},  /* coordinate units code:
		     for previoius four entries
		     1 = length (meters or feet)
		     2 = seconds of arc (in this case, the
		     X values are unsigned intitude and the Y values
		     are latitude, a positive value designates
		     the number of seconds east of Greenwich
		     or north of the equator 88 */

    {"wevel",   2},  

    {"swevel",  2},  

    {"sut",     2},  

    {"gut",     2},  

    {"sstat",   2},  

    {"gstat",   2},  

    {"tstat",   2},  

    {"laga",    2},  /* lag time A, time in ms between end of 240-
		      byte trace identification header and time
		      break, positive if time break occurs after
		      end of header, time break is defined as
		      the initiation pulse which maybe recorded
		      on an auxiliary trace or as otherwise
		      specified by the recording system 104 */

    {"lagb",    2},  /* lag time B, time in ms between the time
		      break and the initiation time of the energy source,
		      may be positive or negative 106 */

    {"delrt",   2},  /* delay recording time, time in ms between
		      initiation time of energy source and time
		      when recording of data samples begins
		      (for deep water work if recording does not
		      start at zero time) 108 */

    {"muts",    2},  

    {"mute",    2},  

    {"ns",      2},  

    {"dt",      2},  

    {"gain",    2},  /* gain type of field instruments code:
		      1 = fixed
		      2 = binary
		      3 = floating point
		      4 ---- N = optional use 118 */

    {"igc",    2},   

    {"igi",    2},   

    {"corr",   2},   /* correlated:
		      1 = no
		      2 = yes 124 */    

    {"sfs",    2},   

    {"sfe",    2},   

    {"slen",   2},   

    {"styp",   2},   /* sweep type code:
		      1 = linear
		      2 = cos-squared
		      3 = other 132 */   

    {"stas",   2},   

    {"stae",   2},   

    {"tatyp",  2},   

    {"afilf",  2},   

    {"afils",  2},   

    {"nofilf", 2},   

    {"nofils", 2},   

    {"lcf",    2},   

    {"hcf",    2},   

    {"lcs",    2},   

    {"hcs",    2},   

    {"year",   2},   

    {"day",    2},   

    {"hour",   2},   

    {"minute", 2},   

    {"sec",    2},   

    {"timbas", 2},   /* time basis code:
		      1 = local
		      2 = GMT
		      3 = other 166 */   

    {"trwf",   2},   /* trace weighting factor, defined as 1/2^N
		      volts for the least sigificant bit 168 */

    {"grnors", 2},   /* geophone group number of roll switch
		      position one 170 */

    {"grnofr", 2},   /* geophone group number of trace one within
		      original field record 172 */

    {"grnlof", 2},   /* geophone group number of last trace within
		      original field record 174 */

    {"gaps",   2},   

    {"otrav",  2},   /* overtravel taper code:
		      1 = down (or behind)
		      2 = up (or ahead) 71/178 */
    {"cdpx",   4},   
    {"cdpy",   4},   
    {"iline",  4},   
    {"xline",  4},   
    {"shnum",  4},   
    {"shsca",  2},   
    {"tval",   2},   
    {"tconst4",4},   
    {"tconst2",2},   
    {"tunits", 2},   
    {"device", 2},   
    {"tscalar",2},   
    {"stype",  2},   
    {"sendir", 4},   
    {"unknown",2},   
    {"smeas4", 4},   
    {"smeas2", 2},   
    {"smeasu", 2},   
    {"unass1", 4},   
    {"unass2", 4}    

])



	
class segy_file_header(tb.IsDescription):
	TFH1 = tb.StringCol(80)
	TFH2 = tb.StringCol(80)
	TFH3 = tb.StringCol(80)
	TFH4 = tb.StringCol(80)
	TFH5 = tb.StringCol(80)
	TFH6 = tb.StringCol(80)
	TFH7 = tb.StringCol(80)
	TFH8 = tb.StringCol(80)
	TFH9 = tb.StringCol(80)
	TFH10 = tb.StringCol(80)
	TFH11 = tb.StringCol(80)
	TFH12 = tb.StringCol(80)
	TFH13 = tb.StringCol(80)
	TFH14 = tb.StringCol(80)
	TFH15 = tb.StringCol(80)
	TFH16 = tb.StringCol(80)
	TFH17 = tb.StringCol(80)
	TFH18 = tb.StringCol(80)
	TFH19 = tb.StringCol(80)
	TFH20 = tb.StringCol(80)
	TFH21 = tb.StringCol(80)
	TFH22 = tb.StringCol(80)
	TFH23 = tb.StringCol(80)
	TFH24 = tb.StringCol(80)
	TFH25 = tb.StringCol(80)
	TFH26 = tb.StringCol(80)
	TFH27 = tb.StringCol(80)
	TFH28 = tb.StringCol(80)
	TFH29 = tb.StringCol(80)
	TFH30 = tb.StringCol(80)
	TFH31 = tb.StringCol(80)
	TFH32 = tb.StringCol(80)
	TFH33 = tb.StringCol(80)
	TFH34 = tb.StringCol(80)
	TFH35 = tb.StringCol(80)
	TFH36 = tb.StringCol(80)
	TFH37 = tb.StringCol(80)
	TFH38 = tb.StringCol(80)
	TFH39 = tb.StringCol(80)
	TFH40 = tb.StringCol(80)
	
segy_textual_file_header = np.dtype([
('TFH1', '<a80'),
('TFH2', (np.str_,80)),
('TFH3', (np.str_,80)),
('TFH4', (np.str_,80)),
('TFH5', (np.str_,80)),
('TFH6', (np.str_,80)),
('TFH7', (np.str_,80)),
('TFH8', (np.str_,80)),
('TFH9', (np.str_,80)),
('TFH10', (np.str_,80)),
('TFH11', (np.str_,80)),
('TFH12', (np.str_,80)),
('TFH13', (np.str_,80)),
('TFH14', (np.str_,80)),
('TFH15', (np.str_,80)),
('TFH16', (np.str_,80)),
('TFH17', (np.str_,80)),
('TFH18', (np.str_,80)),
('TFH19', (np.str_,80)),
('TFH20', (np.str_,80)),
('TFH21', (np.str_,80)),
('TFH22', (np.str_,80)),
('TFH23', (np.str_,80)),
('TFH24', (np.str_,80)),
('TFH25', (np.str_,80)),
('TFH26', (np.str_,80)),
('TFH27', (np.str_,80)),
('TFH28', (np.str_,80)),
('TFH29', (np.str_,80)),
('TFH30', (np.str_,80)),
('TFH31', (np.str_,80)),
('TFH32', (np.str_,80)),
('TFH33', (np.str_,80)),
('TFH34', (np.str_,80)),
('TFH35', (np.str_,80)),
('TFH36', (np.str_,80)),
('TFH37', (np.str_,80)),
('TFH38', (np.str_,80)),
('TFH39', (np.str_,80)),
('TFH40', (np.str_,80)),
])
	
segy_binary_file_header = np.dtype([
("jobid",'i4'),	#/* job identification number */
("lino",'i4'),		#/* line number (only one line per reel) */
("reno",'i4'),		#/* reel number */
("ntrpr",'u2'),	#/* number of data traces per record */
("nart",'u2'),		#/* number of auxiliary traces per record */
("hdt",'u2'),		#/* sample interval in micro secs for this reel */
("dto",'u2'),		#/* same for original field recording */
("hns",'u2'),		#/* number of samples per trace for this reel */
("nso",'u2'),		# /* same for original field recording */
("format",'i2'),	#/* data sample format code*/
("fold",'i2'),		#/* CDP fold expected per CDP ensemble */
("tsort",'i2'),	#/* trace sorting code*/
("vscode",'i2'),	#
("hsfs",'i2'),		#
("hsfe",'i2'),		#
("hslen",'i2'),	#
("hstyp",'i2'),	#
("schn",'i2'),		#
("hstas",'i2'),	#
("hstae",'i2'),	#
("htatyp",'i2'),	#
("hcorr",'i2'),	#
("bgrcv",'i2'),	#
("rcvm",'i2'),		#
("mfeet",'i2'),	#
("polyt",'i2'),	#
("vpol",'i2'),		#
("pad","S240"),	#
("revno",'i2'),	#
("fxtrl",'i2'),	#
("next",'i2'),		#
("endpad","S94"),	#
])

if __name__ == "main":
	print segy_binary_file_header

'''
	short format;	:
				1 = floating point, 4 byte (32 bits)
				2 = fixed point, 4 byte (32 bits)
				3 = fixed point, 2 byte (16 bits)
				4 = fixed point w/gain code, 4 byte (32 bits)
				5 = IEEE floating point, 4 byte (32 bits)
				8 = two's complement integer, 1 byte (8 bits)

	short tsort;	: 
				1 = as recorded (no sorting)
				2 = CDP ensemble
				3 = single fold continuous profile
				4 = horizontally stacked 


	short vscode;	/* vertical sum code:
				1 = no sum
				2 = two sum ...
				N = N sum (N = 32,767) */

	short hsfs;	/* sweep frequency at start */

	short hsfe;	/* sweep frequency at end */

	short hslen;	/* sweep length (ms) */

	short hstyp;	/* sweep type code:
				1 = linear
				2 = parabolic
				3 = exponential
				4 = other */

	short schn;	/* trace number of sweep channel */

	short hstas;	/* sweep trace taper length at start if
			   tapered (the taper starts at zero time
			   and is effective for this length) */

	short hstae;	/* sweep trace taper length at end (the ending
			   taper starts at sweep length minus the taper
			   length at end) */

	short htatyp;	/* sweep trace taper type code:
				1 = linear
				2 = cos-squared
				3 = other */

	short hcorr;	/* correlated data traces code:
				1 = no
				2 = yes */

	short bgrcv;	/* binary gain recovered code:
				1 = yes
				2 = no */

	short rcvm;	/* amplitude recovery method code:
				1 = none
				2 = spherical divergence
				3 = AGC
				4 = other */

	short mfeet;	/* measurement system code:
				1 = meters
				2 = feet */

	short polyt;	/* impulse signal polarity code:
				1 = increase in pressure or upward
				    geophone case movement gives
				    negative number on tape
				2 = increase in pressure or upward
				    geophone case movement gives
				    positive number on tape */

	short vpol;	/* vibratory polarity code:
				code	seismic signal lags pilot by
				1	337.5 to  22.5 degrees
				2	 22.5 to  67.5 degrees
				3	 67.5 to 112.5 degrees
				4	112.5 to 157.5 degrees
				5	157.5 to 202.5 degrees
				6	202.5 to 247.5 degrees
				7	247.5 to 292.5 degrees
				8	293.5 to 337.5 degrees */

	short hunass[170];	/* unassigned */
'''
	