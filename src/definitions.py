
#Copyright (c) 2013 Stewart Fletcher
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#the Software, and to permit persons to whom the Software is furnished to do so,
#subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

        
          

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

segy_binary_header=np.dtype([
	('jobid','>i4'),
	('lino','>i4'),
	('reno','>i4'),
	('ntrpr','>i2'),
	('nart','>i2'),
	('hdt','>u2'),
	('dto','>u2'),
	('hns','>u2'),
	('nso','>u2'),
	('format','>i2'),
	('fold','>i2'),
	('tsort','>i2'),
	('vscode','>i2'),
	('hsfs','>i2'),
	('hsfe','>i2'),
	('hslen','>i2'),
	('hstyp','>i2'),
	('schn','>i2'),
	('hstas','>i2'),
	('hstae','>i2'),
	('htatyp','>i2'),
	('hcorr','>i2'),
	('bgrcv','>i2'),
	('rcvm','>i2'),
	('mfeet','>i2'),
	('polyv','>i2'),
	('vpol','>i2'),
	('unassigned_1',(np.str_,240)),
	('segyrev','>i2'),
	('fixedlen','>i2'),
	('numhdr','>i2'),
	('unassigned_2',(np.str_,94)),
])


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
	("tracl",  '>i4'),  
	("tracr",  '>i4'),  
	("fldr",   '>i4'),  
	("tracf",  '>i4'),  
	("ep",     '>i4'),  
	("cdp",    '>i4'),  
	("cdpt",   '>i4'),  
	("trid",   '>i2'),  
	("nvs",    '>i2'),  
	("nhs",    '>i2'), 
	("duse",   '>i2'),  
	("offset", '>i4'), 
	("gelev",  '>i4'), 
	("selev",  '>i4'), 
	("sdepth", '>i4'),  
	("gdel",   '>i4'),  
	("sdel",   '>i4'),  
	("swdep",  '>i4'),  
	("gwdep",  '>i4'),  
	("scalel", '>i2'),  
	("scalco", '>i2'),  
	("sx",     '>i4'),  
	("sy",     '>i4'),  
	("gx",     '>i4'),  
	("gy",     '>i4'),  
	("counit", '>i2'),  
	("wevel",   '>i2'),  
	("swevel",  '>i2'),  
	("sut",     '>i2'),  
	("gut",     '>i2'),  
	("sstat",   '>i2'),  
	("gstat",   '>i2'),  
	("tstat",   '>i2'),  
	("laga",    '>i2'),  
	("lagb",    '>i2'), 
	("delrt",   '>i2'), 
	("muts",    '>i2'),  
	("mute",    '>i2'),  
	("ns",      '>i2'),  
	("dt",      '>i2'),  
	("gain",    '>i2'),  
	("igc",    '>i2'),   
	("igi",    '>i2'),   
	("corr",   '>i2'),  
	("sfs",    '>i2'),   
	("sfe",    '>i2'),   
	("slen",   '>i2'),   
	("styp",   '>i2'),  
	("stas",   '>i2'),   
	("stae",   '>i2'),   
	("tatyp",  '>i2'),   
	("afilf",  '>i2'),   
	("afils",  '>i2'),   
	("nofilf", '>i2'),   
	("nofils", '>i2'),   
	("lcf",    '>i2'),   
	("hcf",    '>i2'),   
	("lcs",    '>i2'),   
	("hcs",    '>i2'),   
	("year",   '>i2'),   
	("day",    '>i2'),   
	("hour",   '>i2'),   
	("minute", '>i2'),   
	("sec",    '>i2'),   
	("timbas", '>i2'),  
	("trwf",   '>i2'),   
	("grnors", '>i2'), 
	("grnofr", '>i2'),  
	("grnlof", '>i2'),   
	("gaps",   '>i2'),   
	("otrav",  '>i2'),   
	("cdpx",   '>i4'),   
	("cdpy",   '>i4'),   
	("iline",  '>i4'),   
	("xline",  '>i4'),   
	("shnum",  '>i4'),   
	("shsca",  '>i2'),   
	("tval",   '>i2'),   
	("tconst4",'>i4'),   
	("tconst2'",'>i2'),   
	("tunits", '>i2'),   
	("device", '>i2'),   
	("tscalar",'>i2'),   
	("stype",  '>i2'),   
	("sendir", '>i4'),   
	("unknown",'>i2'),   
	("smeas4", '>i4'),   
	("smeas2", '>i2'),   
	("smeasu", '>i2'),   
	("unass1", '>i4'),   
	("unass2", '>i4')    

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

	