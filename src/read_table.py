#initial tests to see if pytables is
#suitable for storing seismic data
# sf, 1-jul-2013

import tables as tb
import numpy as np
import su
import definitions as d

	
h5file = tb.openFile("test1.h5", mode = "r")

dataObject = h5file.getNode("/columns", "cdp")