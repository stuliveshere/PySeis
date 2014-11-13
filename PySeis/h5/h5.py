'''
raw segy import into database
'''
import tables as tb
from tables.nodes import filenode
import os
import warnings
warnings.filterwarnings('ignore', category=tb.NaturalNameWarning)
import numpy as np
import sys

filter_ = tb.Filters(complib='zlib', complevel=1)

tfh = np.dtype([('TFH', (np.str_,  80))])

bfh = np.dtype([
    ('jobid', 'i4'),
    ('lino', 'i4'),
    ('reno', 'i4'),
    ('ntrpr', 'i2'), # mandatory (prestack)
    ('nart', 'i2'), # mandatory (prestack)
    ('hdt', 'u2'), # mandatory (all)
    ('dto', 'u2'),
    ('hns', 'u2'), # mandatory (all)
    ('nso', 'u2'),
    ('format', 'i2'), # mandatory (all)
    ('fold', 'i2'), # strongly recommended 
    ('tsort', 'i2'), # strongly recommended 
    ('vscode', 'i2'),
    ('hsfs', 'i2'),
    ('hsfe', 'i2'),
    ('hslen', 'i2'),
    ('hstyp', 'i2'),
    ('schn', 'i2'),
    ('hstas', 'i2'),
    ('hstae', 'i2'),
    ('htatyp', 'i2'),
    ('hcorr', 'i2'),
    ('bgrcv', 'i2'),
    ('rcvm', 'i2'),
    ('mfeet', 'i2'), # strongly recommended 
    ('polyv', 'i2'),
    ('vpol', 'i2'),
    ('unassigned_1', (np.str_,   240)),
    ('segyrev', 'i2'), # mandatory (all)
    ('fixedlen', 'i2'), # mandatory (all)
    ('numhdr', 'i2'), # mandatory (all)
    ('unassigned_2', (np.str_,   94)),
])

def init(database):  
    db = tb.open_file(database, 'w', title='PySeis')
    db.createGroup(db.root, 'raws', 'raws')
    db.createGroup(db.root.raws, 'segy', 'segy')
    db.createGroup(db.root.raws, 'segd', 'segd')
    db.createGroup(db.root.raws, 'su', 'su')
    return db

def add_raw(db, source, dest):
    fsize = os.path.getsize(source)

    fnode = filenode.new_node(db, where=db.root.raws.segy.files, name=dest, expectedsize=fsize, filters=filter_)
    fnode.write(open(source).read())
    fnode.attrs.tape_format="segy"
    fnode.close()
    
def extract_EBCDIC(leaf):
    ''''function to read EBCDIC header'''
    data = leaf[:3200].tostring()
    ascii = data.decode('EBCDIC-CP-BE').encode('ascii')
    return np.fromstring(ascii, dtype=tfh)
 
def extract_BFH(leaf):
    '''assumes format header is set'''
    data =np.frombuffer(leaf[3200:3200+400], dtype=bfh)
    try:
        assert 0 < data['format'] < 9
        return data
    except AssertionError:
        return data.byteswap()
        
def clear_file(leaf):
    '''removes table data while preserving metadata.
    eventually this will allow processing history/
    parameters to be stored and will give the option
    of re-creating the dataset'''
    leaf.truncate(0)

if __name__ == '__main__':
    os.chdir('../../data/')
    path = '/coalStor/University_QLD/crystal_mountain/2014/data/segy/'
    filelist = [a for a in os.listdir(path) if '.segy' in a]
    a = init('segy_test.h5')
    a.createGroup(a.root.raws.segy, 'files', 'segy files')
    for file_ in filelist:
        add_raw(a, path+file_, file_)
    
    a.createGroup(a.root.raws.segy, 'EBCDIC', 'textual file header')
    a.createGroup(a.root.raws.segy, 'BFH', 'binary file header') 
    for leaf in a.root.raws.segy.files._f_iter_nodes(classname='Leaf'):
        name =  leaf.name
        th = extract_EBCDIC(leaf)
        a.create_table(a.root.raws.segy.EBCDIC, name='%s.EBCDIC' %name, description=th, filters=filter_, expectedrows=40)
        bh = extract_BFH(leaf)
        a.create_table(a.root.raws.segy.BFH, name='%s.BFH' %name, description=bh, filters=filter_, expectedrows=1)
 

     
     
     

     
     
     

     
     
     
     
     

