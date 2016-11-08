import su
import numpy as np

class workspace(object):
    '''
    holds the data object and associated methods
    '''
    def __init__(self):
        self.data = None
        
    def load(self, file, format="npy"):
        '''
        initialises a file
        i.e. memmaps the SU file to a numpy array.
        '''
        if format == "npy":
            self.data = np.load(file, mmap_mode='r')
        if format == "su":
            _ns = self.getNs(file)
            _type =self. build_dtype(_ns)
            self.data =  np.memmap(file, dtype=_type, mode='r')
        
    def getNs(self, file):
        '''
        reaches into the SU file and reads the number of samples
        fom the first trace header.
        '''
        return np.fromfile(file, dtype=su.traceHeaderDtype, count=1)['ns']
    
    def build_dtype(self, _ns):
        '''
        builds a numpy dtype as defined
        in format. 
        '''
        return np.dtype(su.traceHeaderDtype.descr + [('data', ('<f4',_ns))])
        
    def new(self, _ns):
        pass
        
    def save(self, file, format="npy"):
        if format == "npy":
            np.save(file, self.data)
        if format == "su":
            self.data.tofile(file)
        
    
if __name__ == "__main__":
    pass