import format
import numpy as np

class workspace(object):
    '''
    holding class for launching su file
    '''
    def __init__(self):
        self.ns = None
        self.dtype = None
        self.data = None
        
    def initialise(self, filename, fileType="su"):
        if fileType == "su":
            self.ns = self.getNs(filename)
            self.dtype = np.dtype(format.traceHeaderDtype.descr + [('data', ('<f4',self.ns))])
            self.data =  np.memmap(filename, dtype=self.dtype, mode='r')
        
    def getNs(self, filename):
        return np.fromfile(filename, dtype=format.traceHeaderDtype, count=1)['ns']
        
    def new(self, ns):
        pass
    
    