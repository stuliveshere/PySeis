from __future__ import print_function #python 3
import tables as tb
import cProfile
import time
import numpy as np


class Timer:    
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start

def dups1(th):
	with Timer() as t:
		for row in th:
			id = row['id']
			counts = row['counts']
			query = '(id == %d) & (counts == %d)' %(id, counts)
			result = th.readWhere(query)
			if len(result) > 1:
				#~ print(row['id'], row['counts'])
				pass
	#~ print('''
	#~ brute force method
	#~ with row looksups
	#~ rectangular search
	#~ nrows=%d
	#~ time = %.3fs
	#~ ''') %(th.nrows, t.interval)
		
		
def dups2(th):
	with Timer() as t:
		
		for row in th:
			id = row['id']
			counts = row['counts']
			query = '(id == %d) & (counts == %d)' %(id, counts)
			result = th.readWhere(query, start=row.nrow, stop=th.nrows)
			if len(result) > 1:
				print(row['id'])
	print('''
	brute force method
	triangular search
	row lookups
	nrows=%d
	time = %.3fs	
	
	''') %(th.nrows, t.interval)


def dups3(th):
	with Timer() as t:
		for row in th:
			result = th.readWhere('(id == cid) & (counts == ccounts)', {'cid': row['id'], 'ccounts': row['counts']})
			if len(result) > 1:
				print(row['id'])
	print('''
	brute force method
	rectangular search
	with condvals
	nrows=%d
	time = %.3fs	
	
	''')%(th.nrows, t.interval)
			
def dups4(th):
	th.cols.id.remove_index()
	th.cols.counts.remove_index()
	indexrows = th.cols.id.create_csindex(filters=filters)
	indexrows = th.cols.counts.create_csindex(filters=filters)
	for row in th:
		result = th.readWhere('(id == cid) & (counts == ccounts)', {'cid': row['id'], 'ccounts': row['counts']}, start=row.nrow, stop=th.nrows)
		if len(result) > 1:
			pass
			#~ print(row['id'])


			
def dups5(th):
	''' 
	iterator only
	'''
	iters = []
	with Timer() as t:
		for row in th:
			result = th.where('(id == cid) & (counts == ccounts)', {'cid': row['id'], 'ccounts': row['counts']})
	print( '''
	brute force method
	iterator only
	with condvals
	nrows=%d
	time = %.3fs	
	
	''')%(th.nrows, t.interval)

def dups6(th):
	'''
	bloom filter
	'''

	ex = tb.Expr('(x * 65536) + y', uservars = {"x": th.cols.id, "y":  th.cols.counts})
	ex.setOutput(th.cols.hash)
	ex.eval()
	th.cols.hash.remove_index()
	th.cols.hash.create_csindex(filters=filters)
	ref = None
	dups = []
	for row in th.itersorted(sortby=th.cols.hash):
		if row['hash'] == ref:
			dups.append(row['hash'] )
		ref = row['hash']
	if dups:
		pass
		#~ print("ids: ", np.right_shift(np.array(dups, dtype=np.int64), 16))
		#~ print("counts: ", np.array(dups, dtype=np.int64) & 65536-1)

	
def dups7(th):

	ex = tb.Expr('(x * 65536) + y', uservars = {"x": th.cols.id, "y":  th.cols.counts})
	ex.setOutput(th.cols.hash)
	ex.eval()
	th.cols.hash1[1:] = th.cols.hash[:-1]
	th.cols.hash1[0] = th.cols.hash[-1]
	ex = tb.Expr('(x - y)', uservars = {"x": th.cols.hash, "y":  th.cols.hash1})
	result = th.where('hash == hash1', {'cid': row['id'], 'ccounts': row['counts']})
	#~ ref = None
	#~ dups = []
	#~ for row in th.itersorted(sortby=th.cols.hash):
		#~ if row['hash'] == ref:
			#~ dups.append(row['hash'] )
		#~ ref = row['hash']
	#~ if dups:
		#~ print("ids: ", np.right_shift(np.array(dups, dtype=np.int64), 16))
		#~ print("counts: ", np.array(dups, dtype=np.int64) & 65536-1)

	

def dups8(db):
	'''
	sorted
	'''
	th = db.root.line.TH
	#~ node1 = db.createGroup("/", 'line1', 'Node1')
	
	#~ mytype = np.dtype([('hash', np.int64)])
	#~ filters = tb.Filters(complib='blosc', complevel=1)
	#~ db = tb.openFile('db2.h5', mode = "w", title='test')
	#~ node = db.createGroup("/", 'line', 'Node')
	#~ dh = db.createTable(node, 'DH', mytype, "Headers", expectedrows=th.nrows, filters=filters)
	
	#~ 
	
	ex = tb.Expr('(x * 65536) + y', uservars = {"x": th.cols.id, "y":  th.cols.counts})
	ex.setOutput(th.cols.hash)
	ex.eval()
	
	th.cols.hash.remove_index()
	th.cols.hash.create_csindex(filters=filters)
	#~ tt = th.copy(newparent=node1, sortby=th.cols.hash)
	db.copy_file('test.h5', sortby=th.cols.hash, overwrite=True)
	
	print(th)
	#~ print(tt)

		
		#~ z.next()
	#~ th.cols.hash1[1:] = th.cols.hash[:-1]
	#~ th.cols.hash1[0] = th.cols.hash[-1]
	#~ ex = tb.Expr('(x - y)', uservars = {"x": th.cols.hash, "y":  th.cols.hash1})
	#~ ex.setOutput(th.cols.result)
	#~ ex.eval()	
	#~ print(th.readWhere('result == 0'))
	db.close()	
	
def dups9(th):
	''' 
	iterator only
	'''
	iters = []
	with Timer() as t:
		for row in th:
			iters.append(th.get_where_list('(id == cid) & (counts == ccounts)', {'cid': row['id'], 'ccounts': row['counts']}))
		for i in iters:
			if len(i) > 1:
				print(th[i[1]]['id'])
			
		
	print('''
	brute force method
	iterator only
	with condvals
	nrows=%d
	time = %.3fs	
	
	''')%(th.nrows, t.interval)	


if __name__ == '__main__':
	#~ print th.willQueryUseIndexing(condition, condvars=None)
	for n in range(4, 13, 1):
		nrows = int(10**n)
		print("1e%d rows" %n)
		db = tb.openFile('db.h5', mode = "w", title='test')
		node = db.createGroup("/", 'line', 'Node')
		mytype = np.dtype([('id', np.int64),('counts', np.int64), ('hash', np.int64)])
		filters = tb.Filters(complib='blosc', complevel=1)
		th = db.createTable(node, 'TH', mytype, "Headers", expectedrows=nrows, filters=filters)
		remainder =  nrows% 1e6
		chunks = int((nrows - remainder)/1e6)
		for i in range(chunks):
			data = np.random.randint(1, 2**16, (1e6, 3)).astype(np.int64)
			th.append(data)				
		data = np.random.randint(1, 2**16, (remainder, 3)).astype(np.int64)
		th.append(data)
		ex = tb.Expr('0')
		ex.setOutput(th.cols.hash)
		ex.eval()


		#~ dups1(th)
		#~ dups2(th)
		#~ dups3(th)
		#~ dups4(th)
		#~ dups5(th)
		#~ dups6(th)
		#~ dups7(th)
		#~ dups8(db)
		#~ dups9(th)
		import timeit
		#~ print(np.amin(timeit.repeat("dups4(th)", setup="from __main__ import dups4, th", number=1, repeat=1)))
		print(np.amin(timeit.repeat("dups6(th)", setup="from __main__ import dups6, th", number=1, repeat=1)))
		print(np.amin(timeit.repeat("dups8(db)", setup="from __main__ import dups8, db", number=1, repeat=1)))

		db.close()


	