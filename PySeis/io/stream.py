import numpy as np
import time      
import sys
from headers import su_header_dtype


#==================================================
#              timing decorator
#==================================================
import time
def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r %2.2f sec' % \
              (method.__name__,  te-ts)
        return result

    return timed



def build_dtype(_ns):
    '''
    builds a numpy dtype as defined
    in format. 
    '''
    return np.dtype(su_header_dtype.descr + [('trace', ('<f4',_ns))])

def getNs(file):
    '''
    reaches into the SU file and reads the number of samples
    fom the first trace header.
    '''
    return np.fromfile(file, dtype=su_header_dtype, count=1)['ns']

def loadSU(infile, outfile):
    '''
    initialises a file
    i.e. memmaps the SU file to a numpy array.
    '''
    _ns = getNs(infile)
    _type = build_dtype(_ns)
    indata= np.memmap(infile, dtype=_type, mode='r')
    outdata = np.lib.format.open_memmap(outfile, dtype=_type, shape=indata.shape, mode='w+')
    outdata[:] = indata[:]
    outdata.flush()
    
def saveSU(infile, outfile):
    ''' 
    saves npy file infile
    to su file outfile
    '''
    np.lib.format.open_memmap(infile, mode='r').tofile(outfile)
    
        

def update_progress(progress):
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rMb/S: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()
    
class Gather(object):
    '''
    data object which contains 
    
     * the gather to be processed
     * its source and destination (memmapped files)
     * the mask used to extract and save
     '''

    def __init__(self, source, dest, mask):
        self.data = np.array(source[mask])
        self.dest = dest
        self.mask = mask

    def __getitem__(self, i):
        return self.data[i]

    def save(self):
        self.dest[self.mask] = self.data
        
    def close(self):
        self.dest.flush()
        
        

class Stream(object):
    '''
    streams in the seismic data in gathers
    needs the sort order to be definied.
    requires input to be .npy file
    '''

    def __init__(self, infile, outfile, order=['fldr', 'tracf']): #default to shot gathers
        self.primaryOrder = order[0]
        self.secondaryOrder = order[1]
        self.indata = np.lib.format.open_memmap(infile, mode='r')    
        self.outdata = np.lib.format.open_memmap(outfile, dtype=self.indata.dtype, shape= self.indata.shape, mode='w+') 
        self.outdata[:] = self.indata[:]
        self.outdata['trace'].fill(0.0)
        self.outdata.flush()


    def __iter__(self):
        keys = np.unique(self.indata[self.primaryOrder])
        steps = (len(keys)*1.0)
        t = time.time()
        for count, key in enumerate(keys):
            mask = self.indata[self.primaryOrder] == key
            gather = Gather(self.indata, self.outdata, mask)
            gather.data.sort(order=self.secondaryOrder)
            update_progress(gather.data.nbytes*1e-6/time.time()-t)
            t = time.time()
            yield gather
            
    def save(self):
        self.outdata[self.mask] = self.gather

    def close(self):
        del self.outdata
            


        
            

        
        
    
    
