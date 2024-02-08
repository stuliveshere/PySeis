import numpy as np
import time      
import sys


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
        
        

class Flow(object):
    '''
    streams in the seismic data in gathers
    needs the sort order to be defined.
    requires input to be .npy file
    needs a list of method objects designed to 
    take the gathers as structured arrays
    '''

    def __init__(self, infile, outfile=None, order=['fldr', 'tracf'], methods=[]): #default to shot gathers
        self.methods = methods
        self.primaryOrder = order[0]
        self.secondaryOrder = order[1]
        self.indata = np.memmap(infile, mode='r')
        if outfile:   
            self.outdata = np.memmap(outfile, dtype=self.indata.dtype, shape= self.indata.shape, mode='w+') 
            #self.outdata[:] = self.indata[:]
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

    def run(self):
        '''iterates a series of gathers through the methods defined in the input.
        if no methods are definied make a copy of the data
        this is a test 201811231427'''
        for gather in self:
            pass
            
            
        
        

    def close(self):
        del self.outdata
            


        
            

        
        
    
    
