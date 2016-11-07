import numpy as np
import pylab

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
        


    
    
