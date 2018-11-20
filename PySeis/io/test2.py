'''
Created on 20 Nov. 2018

@author: sfletcher
'''

import numpy as np

class Chunker(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
    def blockHeaders(self):
        self.blockHeaderMethods = []
        
            
    def chunker(self):
        pass

        
    def read(self):
        pass
    
class Segy(Chunker):
    def blockHeaders(self):
        
        
        def read_EBCDIC(_file):
            ''''function to read EBCDIC header'''
            with open(_file, 'rb') as f:
                header = np.fromfile(f, dtype='u2', count=3200/2)
                if np.any(np.diff(header)): #check for content
                    f.seek(0)
                    return f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
                else:
                    return None
    
        def read_bheader(_file):
            ''''function to read binary header'''
            segy_binary_header_dtype = np.dtype([
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
            with open(_file, 'rb') as f:
                f.seek(3200)
                binary = np.fromstring(f.read(400), dtype=segy_binary_header_dtype)
                #endian sanity checks. this is pretty crude and will need revisting.
                try:
                    assert 0 < binary['format'] < 9
                except AssertionError:
                    binary = binary.byteswap()
                return binary
            
        self.blockHeaderMethods = [read_EBCDIC, read_bheader]
        
    