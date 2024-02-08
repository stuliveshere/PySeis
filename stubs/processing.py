import numpy as np
from toolbox import io
import toolbox
import pylab
from scipy.signal import butter, lfilter, convolve2d
from scipy.interpolate import RectBivariateSpline as RBS
from scipy.interpolate import interp2d
#~ from matplotlib.mlab import griddata
import numpy.ma as ma


def initialise(file):
        #intialise empty parameter dictionary
        #kwargs stands for keyword arguments
        kwargs = {}
        #load file
        dataset = toolbox.read(file)
        
        
        
        #allocate stuff
        #~ 
        ns = kwargs['ns'] = dataset['ns'][0]
        dt = kwargs['dt'] = dataset['dt'][0]/1e6
        
                       
        #also add the time vector - it's useful later
        kwargs['times'] = np.arange(0, dt*ns, dt)
        
        dataset['trace'] /= np.amax(dataset['trace'])
        dataset['tracr'] = np.arange(dataset.size)
        
        kwargs['primary'] = 'cdp'
        kwargs['secondary'] = 'offset'
        kwargs['cdp'] = np.sort(np.unique(dataset['cdp']))
        kwargs['step'] = 1
        
        toolbox.scan(dataset)
        return dataset, kwargs
        
@io
def tar(data, **kwargs):
        #pull some values out of the
        #paramter dictionary
        gamma = kwargs['gamma']
        t = kwargs['times']
        
        #calculate the correction coeffieicnt
        r  = np.exp(gamma * t)
        
        #applyt the correction to the data
        data['trace'] *= r
        return data

def build_vels(vels, **kwargs):
        from scipy import interpolate
        

        cdps = np.array(kwargs['cdp'])
        times = np.array(kwargs['times'])	
        keys = vels.keys()
        x = []
        t = []
        values = []
        for i in vels.items():
                cdp = i[0]
                picks= i[1]
                for pick in picks:
                        x.append(cdp)
                        t.append(pick[0])
                        values.append(pick[1])
        
        grid_x, grid_y = np.meshgrid(cdps, times)	

        #top left
        x.append(min(cdps))
        t.append(min(times))
        values.append(min(values))
        
        #top right
        t.append(min(times))
        x.append(max(cdps))
        values.append(min(values))
        
        #bottom left
        x.append(min(cdps))
        t.append(max(times))
        values.append(max(values))
        
        #bottom right
        t.append(max(times))
        x.append(max(cdps))
        values.append(max(values))
        
        zi = pylab.griddata(x, t, values, grid_x, grid_y, interp='linear')
        
        #~ zi = griddata((np.array(x), np.array(t)), values.flatten(), (grid_x, grid_y), method='nearest')
        #~ window = 50
        #~ filter = np.ones((window,window), 'f')/(1.0*window**2)
        #~ zi = convolve2d(zi, filter, boundary='symm', mode='same')
        
        return zi.T

                


def _nmo_calc(tx, vels, offset):
        '''calculates the zero offset time'''
        t0 = np.sqrt(tx*tx - (offset*offset)/(vels*vels))
        return t0
        
@io
def nmo(dataset, **kwargs):
        offsets = np.unique(dataset['offset'])
        if 'smute' not in kwargs.keys(): kwargs['smute'] = 10000.
        ns = kwargs['ns']
        dt = kwargs['dt'] 
        tx = kwargs['times']
        
        for offset in offsets:

                aoffset = np.abs(offset.astype(np.float))
                #calculate time shift for each sample in trac
                t0 = _nmo_calc(tx, kwargs['vels'], aoffset)
                t0 = np.nan_to_num(t0)
                #calculate stretch between each sample
                stretch = 100.0*(np.pad(np.diff(t0),(0,1), 'reflect')-dt)/dt
                mute = kwargs['smute']
                filter = [(stretch >0.0) & ( stretch < mute)]
                inds = [dataset['offset'] == offset]
                subset = np.apply_along_axis(lambda m: np.interp(tx, t0, m), axis=-1, arr=dataset['trace'][inds])

                
                #~ subset[:,tx < np.amin(t0[filter])]  = 0.0
                #~ subset[:,tx > np.amax(t0[filter])] = 0.0
                dataset['trace'][inds] = subset * filter

        return dataset




@io
def co_nmo(dataset, **kwargs):
        offsets = np.unique(np.abs(dataset['offset']))
        cdps = np.sort(np.unique(dataset['cdp']))
        ns = kwargs['ns']
        dt = kwargs['dt'] 
        tx = kwargs['times']	
        if 'smute' not in kwargs.keys(): kwargs['smute'] = 10000.
        
        output = dataset.copy()
        output['trace'].fill(0.0)
        for offset in offsets:
                print offset
                aoffset = np.abs(offset.astype(np.float))
                #~ #calculate time shift for each sample in offset
                t0 = _nmo_calc(tx, kwargs['vels'], aoffset)
                t0 = np.nan_to_num(t0)
                stretch = 100.0*(np.pad(np.diff(t0),(0,1), 'reflect')-dt)/dt
                
                subset = dataset[np.abs(dataset['offset']) == aoffset]
                for trace in np.nditer(subset):
                        cdp = trace['cdp']
                        i = np.where(cdps == cdp)
                        tnew = t0[i,:].flatten()
                        s = np.zeros_like(stretch[i,:])
                        s[(stretch[i,:] >0.0) & ( stretch[i,:] < kwargs['smute'])] = 1
                
                        output['trace'][trace['tracr'],:] = np.interp(tx, tnew, trace['trace']) *s.flatten()
                        
        return output		
                
                
                

def _stack_gather(gather):
        '''stacks a single gather into a trace.
        uses header of first trace. normalises
        by the number of traces'''
        gather['trace'][0] = np.sum(gather['trace'], axis=-2)/np.sqrt(gather.size)
        return gather[0]

@io	
def stack(dataset, **kwargs):
        cdps = np.unique(dataset['cdp'])
        sutype = np.result_type(dataset)
        result = np.zeros(cdps.size, dtype=sutype)
        for index, cdp in enumerate(cdps):
                gather = dataset[dataset['cdp'] == cdp]
                trace = _stack_gather(gather)
                result[index] = trace
        return result


def semb(workspace,**kwargs):
        print ''
        def onclick(e):
                print "(%.2f, %.2f) ," %(e.ydata, e.xdata), 
        vels = kwargs['velocities']
        nvels = vels.size
        ns = kwargs['ns']
        result = np.zeros((nvels,ns),'f')
        loc = np.mean(workspace['cdp'])
        for v in range(nvels):
                panel = workspace.copy()
                kwargs['vels'] = np.ones(kwargs['ns'], 'f') * vels[v]
                nmo(panel, None, **kwargs)
                result[v,:] += np.abs(_stack_gather(panel)['trace'])
        result = result[:,::kwargs['smoother']]
        
        window = 5
        filter = np.ones((window,window), 'f')/(1.0*window**2)
        result = convolve2d(result, filter, boundary='symm', mode='same')

        
        x = vels
        y = np.arange(ns)[::kwargs['smoother']]
        f = RBS(x, y, result, s=0)
        result = f(x, np.arange(ns))
        
        pylab.imshow(result.T, aspect='auto', extent=(min(vels), max(vels),kwargs['ns']*kwargs['dt'],0.), cmap='jet')
        pylab.xlabel('velocity')
        pylab.ylabel('time')
        pylab.title("cdp = %d" %np.unique(loc)) 
        pylab.colorbar()
        fig = pylab.gcf()
        fig.canvas.mpl_connect('button_press_event', onclick)
        print "vels[%d] = " %np.unique(loc), 
        pylab.show()


def _lmo_calc(aoffset, velocity):
        t0 = -1.0*aoffset/velocity
        return t0
        
@io
def lmo(dataset, **kwargs):
        offsets = np.unique(dataset['offset'])
        for offset in offsets:
                aoffset = np.abs(offset)
                shift = _lmo_calc(aoffset, kwargs['lmo'])
                shift  = (shift*1000).astype(np.int)
                inds= [dataset['offset'] == offset]
                dataset['trace'][inds] =  np.roll(dataset['trace'][inds], shift, axis=-1) #results[inds]
        return dataset


@io
def trace_mix(dataset, **kwargs):
        ns = kwargs['ns']
        window = np.ones(kwargs['mix'], 'f')/kwargs['mix']
        for i in range(ns):
                dataset['trace'][:,i] = np.convolve(dataset['trace'][:,i], window, mode='same')
        return dataset
        

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y	

@io
def bandpass(dataset, **kwargs):
        
        # Sample rate and desired cutoff frequencies (in Hz).
        fs = 1./kwargs['dt']
        lowcut = kwargs['lowcut']
        highcut = kwargs['highcut']
            
        dataset['trace'] = butter_bandpass_filter(dataset['trace'], lowcut, highcut, fs, order=6)
        return dataset
        
