from PySeis.segy import segy
import numpy as np
import tables as tb

path = '/oilStor/Origin/Dalwogan_Condabri_3D_2013/processing/segy_out/'

sgy = '5D_PSTM_2s_az15.sgy'

a = segy('test.h5')
a.read([path+sgy])

#~ fileh = tb.open_file("test.h5", mode = "r")

#~ # Get the HDF5 root group
#~ td = fileh.root.jobname.gather0
#~ td.cols.offset.createCSIndex()

#~ for row in td:
	#~ print dir(row)
	#~ break
		
	



