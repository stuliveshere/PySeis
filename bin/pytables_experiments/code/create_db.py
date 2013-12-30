import tables as tb
import numpy as np
import cProfile
	
def create1():
	nrows = int(1e5)
	db = tb.openFile('db_cs.h5', mode = "w", title='test')
	node = db.createGroup("/", 'line', 'Node')
	mytype = np.dtype([('id', np.int32),('counts', np.int32)])
	filters = tb.Filters(complib='blosc', complevel=1)
	th = db.createTable(node, 'TH', mytype, "Headers", expectedrows=nrows, filters=filters)
	
	
	data = np.random.randint(1, 2**16, (nrows, 2)).astype(np.int32)
	
	th.append(data)

	
	indexrows = th.cols.id.create_csindex(filters=filters)
	indexrows = th.cols.counts.create_csindex(filters=filters)	
	
	#~ indexrows = th.cols.id.create_index(filters=filters)
	#~ indexrows = th.cols.counts.create_index(filters=filters)		

def create2():
	nrows = int(1e5)
	db = tb.openFile('db_i.h5', mode = "w", title='test')
	node = db.createGroup("/", 'line', 'Node')
	mytype = np.dtype([('id', np.int32),('counts', np.int32)])
	filters = tb.Filters(complib='blosc', complevel=1)
	th = db.createTable(node, 'TH', mytype, "Headers", expectedrows=nrows, filters=filters)
	
	
	data = np.random.randint(1, 2**12, (nrows, 2)).astype(np.int32)
	
	th.append(data)

	
	#~ indexrows = th.cols.id.create_csindex(filters=filters)
	#~ indexrows = th.cols.counts.create_csindex(filters=filters)	
	
	indexrows = th.cols.id.create_index(filters=filters)
	indexrows = th.cols.counts.create_index(filters=filters)
	
if __name__ == '__main__':
	#~ cProfile.run('create()')
	create1()