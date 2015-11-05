import PySeis.h5.h5 as h5
import PySeis.processing.processing as p

filename = '../data/su_test.h5'

db = h5.pyseis(filename)

for gather in db.db.listNodes('/jobname', classname='Table'):
    p.ximage(gather.cols.data[:], agc=1)
    



