import pylab
import numpy as np
import scipy.signal


def xwigb(panel, key='offset'):
    '''
    looks like suxwigb
    '''
    axis = np.arange(panel['ns'][0])*panel['dt'][0]*1e-6
    traces = panel['trace']
    traces  /= np.sqrt((traces ** 2).sum(1))[:,np.newaxis]
    x, y = np.meshgrid(range(traces.shape[0]), range(traces.shape[1]))
    traces += x.T
    fig = pylab.figure()
    for trace in traces:
        pylab.plot(trace, axis,'k')
    pylab.gca().invert_yaxis()
    pylab.ylabel('Time(s)')
    pylab.title('Trace')
    pylab.gca().xaxis.tick_top()
    pylab.show()

def ximage(data, agc=0):
    '''
    looks like suximage.
    fix this to use the SU
    headers for plotting
    '''
 
    if agc:
        amp_func = agc_func(data=data,window=100)
        data /= amp_func

    fig = pylab.figure()
    pylab.imshow(data.T, aspect='auto', vmin=-1, vmax=1, cmap='gist_yarg') #,
    #extent=(min(panel['offset']), max(panel['offset']), panel['ns'][0]*(panel['dt'][0]*1e-6), 0))
    pylab.xlabel('Offset')
    pylab.ylabel('Time(s)')
    pylab.show()
    
    
def agc_func(data, window):
    vec = np.ones(window)/(window/2.)
    func = np.apply_along_axis(lambda m: np.convolve(np.abs(m), vec, mode='same'), axis=1, arr=data)
    print func
    return func
    
    