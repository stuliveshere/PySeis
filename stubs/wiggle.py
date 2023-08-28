import numpy as np
import numpy.ma as ma
from matplotlib import collections
import toolbox
import pylab
import time
from functools import wraps
  
def timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print ("Total time running %s: %s seconds" %
               (function.func_name, str(t1-t0))
               )
        return result
    return function_timer

@timer
def wiggle(frame, scale=1.0):
        fig = pylab.figure()
        ax = fig.add_subplot(111)        
        ns = frame['ns'][0]
        nt = frame.size
        scalar = scale*frame.size/(frame.size*0.2) #scales the trace amplitudes relative to the number of traces
        frame['trace'][:,-1] = np.nan #set the very last value to nan. this is a lazy way to prevent wrapping
        vals = frame['trace'].ravel() #flat view of the 2d array.
        vect = np.arange(vals.size).astype(np.float) #flat index array, for correctly locating zero crossings in the flat view
        crossing = np.where(np.diff(np.signbit(vals)))[0] #index before zero crossing
        #use linear interpolation to find the zero crossing, i.e. y = mx + c. 
        x1=  vals[crossing]
        x2 =  vals[crossing+1]
        y1 = vect[crossing]
        y2 = vect[crossing+1]
        m = (y2 - y1)/(x2-x1)
        c = y1 - m*x1       
        #tack these values onto the end of the existing data
        x = np.hstack([vals, np.zeros_like(c)])
        y = np.hstack([vect, c])
        #resort the data
        order = np.argsort(y) 
        #shift from amplitudes to plotting coordinates
        x_shift, y = y[order].__divmod__(ns)
        ax.plot(x[order] *scalar + x_shift + 1, y, 'k')
        x[x<0] = np.nan
        x = x[order] *scalar + x_shift + 1
        ax.fill(x,y, 'k', aa=True) 
        ax.set_xlim([0,nt])
        ax.set_ylim([ns,0])
        pylab.tight_layout()
        pylab.show()
        
        
if __name__ == "__main__":
        file = "/home/stewart/su/2d_land_data/2D_Land_data_2ms/su/Line_001.su"
        #file = "/home/sfletcher/Downloads/2d_land_data/2D_Land_data_2ms/Line_001.su"
        data, params = toolbox.initialise(file)
        eps = np.unique(data['ep'])
        for ep in eps[:1]:
                frame = data[data['ep'] == ep]
                params['window'] = 500
                toolbox.agc(frame, None, **params)
                wiggle(frame, scale=2)

    
    
    #~ trace_centers = np.linspace(1,284, panel.size).reshape(-1,1)
    #~ scalar = 284/(panel.size*0.1)
        
    #~ panel['trace'][:,-1] = np.nan
    #~ x = panel['trace'].ravel()
    #~ y = np.arange(x.size)
     
    #~ dx = np.signbit(x)
    #~ before = np.where(np.diff(np.signbit(x)))[0]
    #~ after = before + 1

   #~ #y = mx + c. 
    #~ x1=  x[before].astype(np.float)
    #~ x2 =  x[after].astype(np.float)
    #~ y1 = y[before].astype(np.float)
    #~ y2 = y[after].astype(np.float)
    #~ m = (y2 - y1)/(x2-x1)
    #~ c = y1 - m*x1
    
    #~ xx = np.hstack([x, np.zeros_like(c)])
    #~ yy = np.hstack([y, c])
    #~ inds = np.argsort(yy)
    
    #~ xxx = xx[inds]
    #~ yyy = yy[inds]
    #~ q, r = yyy.__divmod__(1501)
    
    #~ xxx[xxx < 0] = np.nan
    
    #~ xxx = xxx*scalar+q+1
    


    #~ fig = pylab.figure()
    #~ ax = fig.add_subplot(111)
    #~ ax.fill(xxx,r, 'k') 
    #~ ax.plot(xx[inds]*scalar+q+1, r, 'k')
    #~ pylab.xlim([0,284])
    #~ pylab.ylim([0,1500])
    #~ ax.set_ylim(ax.get_ylim()[::-1])
    #~ pylab.tight_layout()
    #~ pylab.show()