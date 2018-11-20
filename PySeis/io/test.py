#testing a proper inheritance structure for streaming input of seismic files
#chunk/yield format with handling for:
#	1) block headers (segy, segs)
#	2) trace header storage
#	3) byte conversion (segy)

class Stream(object):
	pass