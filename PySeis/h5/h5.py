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

th_type = np.dtype([
    ('tracl',  'i4'), # strongly recommended 
    ('tracr',  'i4'),
    ('fldr',   'i4'), # strongly recommended 
    ('tracf',  'i4'), # strongly recommended 
    ('ep',     'i4'),
    ('cdp',    'i4'),
    ('cdpt',   'i4'),
    ('trid',   'i2'), # strongly recommended 
    ('nvs',    'i2'),
    ('nhs',    'i2'),
    ('duse',   'i2'),
    ('offset', 'i4'),
    ('gelev',  'i4'),
    ('selev',  'i4'),
    ('sdepth', 'i4'),
    ('gdel',   'i4'),
    ('sdel',   'i4'),
    ('swdep',  'i4'),
    ('gwdep',  'i4'),
    ('scalel', 'i2'),
    ('scalco', 'i2'),
    ('sx',     'i4'),
    ('sy',     'i4'),
    ('gx',     'i4'),
    ('gy',     'i4'),
    ('counit', 'i2'),
    ('wevel',   'i2'),
    ('swevel',  'i2'),
    ('sut',     'i2'),
    ('gut',     'i2'),
    ('sstat',   'i2'),
    ('gstat',   'i2'),
    ('tstat',   'i2'),
    ('laga',    'i2'),
    ('lagb',    'i2'),
    ('delrt',   'i2'),
    ('muts',    'i2'),
    ('mute',    'i2'),
    ('ns',      'i2'), # strongly recommended 
    ('dt',      'i2'), # strongly recommended 
    ('gain',    'i2'),
    ('igc',    'i2'),
    ('igi',    'i2'),
    ('corr',   'i2'),
    ('sfs',    'i2'),
    ('sfe',    'i2'),
    ('slen',   'i2'),
    ('styp',   'i2'),
    ('stas',   'i2'),
    ('stae',   'i2'),
    ('tatyp',  'i2'),
    ('afilf',  'i2'),
    ('afils',  'i2'),
    ('nofilf', 'i2'),
    ('nofils', 'i2'),
    ('lcf',    'i2'),
    ('hcf',    'i2'),
    ('lcs',    'i2'),
    ('hcs',    'i2'),
    ('year',   'i2'),
    ('day',    'i2'),
    ('hour',   'i2'),
    ('minute', 'i2'),
    ('sec',    'i2'),
    ('timbas', 'i2'),
    ('trwf',   'i2'),
    ('grnors', 'i2'),
    ('grnofr', 'i2'),
    ('grnlof', 'i2'),
    ('gaps',   'i2'),
    ('otrav',  'i2'),
    ('cdpx',   'i4'),
    ('cdpy',   'i4'),
    ('iline',  'i4'),
    ('xline',  'i4'),
    ('shnum',  'i4'),
    ('shsca',  'i2'),
    ('tval',   'i2'),
    ('tconst4', 'i4'),
    ('tconst2', 'i2'),
    ('tunits', 'i2'),
    ('device', 'i2'),
    ('tscalar', 'i2'),
    ('stype',  'i2'),
    ('sendir', 'i4'),
    ('unknown', 'i2'),
    ('smeas4', 'i4'),
    ('smeas2', 'i2'),
    ('smeasu', 'i2'),
    ('unass1', 'i4'),
    ('unass2', 'i4'),
])

def init(database):  
    ''' initialise a new hdf5 database with template
    groups for segy, segyd, su inputs'''
    db = tb.open_file(database, 'w', title='PySeis')
    db.createGroup(db.root, 'raws', 'raws')
    db.createGroup(db.root.raws, 'segy', 'segy')
    db.createGroup(db.root.raws, 'segd', 'segd')
    db.createGroup(db.root.raws, 'su', 'su')
    return db

def add_raw(db, source, dest):
    '''imports raw file into appropriate group
    for later handling'''
    fsize = os.path.getsize(source)
    fnode = filenode.new_node(db, where=db.root.raws.segy.files, name=dest, expectedsize=fsize, filters=filter_)
    fnode.write(open(source).read())
    fnode.attrs.tape_format="segy"
    fnode.close()
    
def extract_EBCDIC(leaf):
    ''''function to read segy EBCDIC header'''
    data = leaf[:3200].tostring()
    ascii_ = data.decode('EBCDIC-CP-BE').encode('ascii')
    return np.fromstring(ascii_, dtype=tfh)
 
def extract_BFH(leaf):
    '''function to read segy binary header. 
    assumes format header is set correctly'''
    data =np.frombuffer(leaf[3200:3200+400], dtype=bfh)
    try:
        assert 0 < data['format'] < 9
        return data
    except AssertionError:
        return data.byteswap()
        
def extract_th(leaf):
    '''function to extract trace headers
    from segy file. does not yet check data type'''
    ns = np.frombuffer(leaf[3220:3222], dtype='u2').byteswap()
    ts = 240 + ns*4
    start = 3600
    end = leaf.size_in_memory
    nt = (end-start) / (ts)
    header_starts = np.arange(start, end, ts)
    inds= np.hstack([range(a, a+240) for a in header_starts]).flatten()
    headers = np.frombuffer(leaf[inds], dtype=th_type).byteswap()
    return headers
    
def extract_td(leaf):
    def ibm2ieee(ibm):
        s = ibm >> 31 & 0x01 
        exp = ibm >> 24 & 0x7f 
        fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
        ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
        return ieee
    ns = np.frombuffer(leaf[3220:3222], dtype='u2').byteswap()
    ts = 240 + ns*4
    start = 3200+400+240
    end = leaf.size_in_memory
    nt = (end-start) / (ts)
    header_starts = np.arange(start, end, ts)
    inds= np.hstack([range(a, a+ns*4) for a in header_starts]).flatten()
    trace_type=np.dtype([('data',('i4',ns))])
    traces = leaf[inds].astype('i4')
    traces = np.frombuffer(ibm2ieee(traces) , dtype=trace_type)
    return traces
        
def clear_file(leaf):
    '''removes table data whilst preserving metadata.
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
    a.createGroup(a.root.raws.segy, 'TH', 'trace headers') 
    a.createGroup(a.root.raws.segy, 'TD', 'trace data') 
    
    a.create_table(a.root.raws.segy.TH, name='trace_headers', description=th_type, filters=filter_, expectedrows=1e6)
    a.create_table(a.root.raws.segy.TD, name='trace_data', description=np.dtype([('data',('f4',1000))]), filters=filter_, expectedrows=1e6)
    
    for leaf in a.root.raws.segy.files._f_iter_nodes(classname='Leaf'):
        name =  leaf.name
        print name
        text_file_header = extract_EBCDIC(leaf)
        a.create_table(a.root.raws.segy.EBCDIC, name='%s.EBCDIC' %name, description=text_file_header, filters=filter_, expectedrows=40)
        binary_file_header = extract_BFH(leaf)
        a.create_table(a.root.raws.segy.BFH, name='%s.BFH' %name, description=binary_file_header, filters=filter_, expectedrows=1)
        trace_headers = extract_th(leaf)
        a.root.raws.segy.TH.trace_headers.append(trace_headers)
        trace_data = extract_td(leaf)
        a.root.raws.segy.TD.trace_data.append(trace_data)
        #~ print trace_data
        clear_file(leaf)

     
     
     

     
     
     
     
     

