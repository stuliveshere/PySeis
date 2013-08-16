#initial tests to see if pytables is
#suitable for storing seismic data
# sf, 1-jul-2013

import tables as tb
import numpy as np
import su
import definitions as d

	
h5file = tb.openFile("test1.h5", mode = "w", title = "Test file")
group = h5file.createGroup("/", 'line1', 'Line 1 Survey')
table = h5file.createTable(group, 'header', d.SU_header, "Header Example")

#SU input example. firstattempt passed header and trace binaries to a single table
#however it might be better to pass the headers to one table and trace data to another.
#question is, what is the best database key to link headers to traces?

#i guess 

database = table.row

tmp = su.readSU('shot-gathers.su')
for trace in tmp:
	for name in trace.dtype.names:
		database[name] = trace[name]
	database.append()
table.flush()

cdp = [x for x in table.iterrows() if x['cdp'] == 100]