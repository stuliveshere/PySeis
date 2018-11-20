'''
Created on 20 Nov. 2018

@author: sfletcher
'''

import numpy as np
import pandas as pd

class Chunker(object):
    '''
    classdocs
    '''
    def __init__(self, nbytes, start=0):
        self.seek = seek
        self.start = start
    
    def chunker(self):
        pass
    

class SU(Chunker):
    '''
    classdocs
    '''


    def __init__(self, _file):
        '''
        Constructor
        '''
        self.filename = _file
        self.blockHeaderMethods = []
        self.read()
        
    def blockHeaders(self):
        '''
        Constructor
        '''
        print self.blockHeaderMethods
  
        
            
    
        
    def read(self):
        print self.filename
        self.blockHeaders()
    
class Segy(Chunker):
    def __init__(self):
        
      
        
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
        Super().__init__()
        
        
        
if __name__ == "__main__":
    _file = "../../data/sample.su"

    
    