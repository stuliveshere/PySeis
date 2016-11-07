import numpy as np
import toolbox
import pylab
from scipy.signal import butter, lfilter, convolve2d
from scipy.interpolate import RectBivariateSpline as RBS
from scipy.interpolate import interp2d
from scipy.interpolate import interp1d
from scipy.interpolate import griddata 
import matplotlib.patches as patches
import numpy.ma as ma
import sys

import warnings
warnings.filterwarnings("ignore")

class DraggablePoint:
    lock = None #only one can be animated at a time
    def __init__(self, point):
        self.point = point
        self.press = None
        self.background = None

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.button == 3:
                if event.inaxes != self.point.axes: return
                if DraggablePoint.lock is not None: return
                contains, attrd = self.point.contains(event)
                if not contains: return
                self.press = (self.point.center), event.xdata, event.ydata
                DraggablePoint.lock = self

                # draw everything but the selected rectangle and store the pixel buffer
                canvas = self.point.figure.canvas
                axes = self.point.axes
                self.point.set_animated(True)
                canvas.draw()
                self.background = canvas.copy_from_bbox(self.point.axes.bbox)

                # now redraw just the rectangle
                axes.draw_artist(self.point)

                # and blit just the redrawn area
                canvas.blit(axes.bbox)

    def on_motion(self, event):
        if DraggablePoint.lock is not self:
            return
        if event.inaxes != self.point.axes: return
        self.point.center, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.point.center = (self.point.center[0]+dx, self.point.center[1]+dy)

        canvas = self.point.figure.canvas
        axes = self.point.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.point)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_release(self, event):
        'on release we reset the press data'
        if DraggablePoint.lock is not self:
            return

        self.press = None
        DraggablePoint.lock = None

        # turn off the rect animation property and reset the background
        self.point.set_animated(False)
        self.background = None

        # redraw the full figure
        self.point.figure.canvas.draw()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.point.figure.canvas.mpl_disconnect(self.cidpress)
        self.point.figure.canvas.mpl_disconnect(self.cidrelease)
        self.point.figure.canvas.mpl_disconnect(self.cidmotion)

def initialise(file, memmap=False, scan=False):
        #intialise empty parameter dictionary
        #kwargs stands for keyword arguments
        kwargs = {}
        #load file
        if memmap == True:
                ns = np.fromfile(file, dtype=toolbox.su_header_dtype, count=1)['ns']
                sutype = toolbox.typeSU(ns)
                dataset = np.memmap(file, dtype=sutype)
        else:
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
        
        if scan:
                toolbox.scan(dataset)
        return dataset, kwargs
        

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


def apply_statics(data, **kwargs):
        for trace in data:
                shift = trace['tstat']/(kwargs['dt']*1000).astype(np.int)
                if shift > 0:
                        trace['trace'][-shift:] = 0
                if shift < 0:
                        trace['trace'][:-shift] = 0
                trace['trace'] = np.roll(trace['trace'] , shift)
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
                        t.append(pick[1])
                        values.append(pick[0])
        
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
        
        
        return zi.T


def _nmo_calc(tx, vels, offset):
        '''calculates the zero offset time'''
        t0 = np.sqrt(tx*tx - (offset*offset)/(vels*vels))
        return t0
        

def old_nmo(dataset, **kwargs):
        if 'smute' not in kwargs.keys(): kwargs['smute'] = 10000.
        ns = kwargs['ns']
        dt = kwargs['dt'] 
        tx = kwargs['times']
        minCdp = np.amin(dataset['cdp'])
        counter = 0
        ntraces = dataset.size
        print "moving out %d traces" %ntraces
        result = dataset.copy()
        result['trace'] *= 0

        
        for i in range(dataset.size):
                trace = dataset[i]
                counter += 1
                if counter > 1000:
                        ntraces -= counter
                        counter = 0
                        print ntraces
                aoffset = np.abs(trace['offset'].astype(np.float))
                cdp = trace['cdp']
                vel = kwargs['vels'][cdp - minCdp]
                #calculate time shift for each sample in trac
                t0 = _nmo_calc(tx, vel, aoffset)
                t0 = np.nan_to_num(t0)

                #calculate stretch between each sample
                stretch = 100.0*(np.pad(np.diff(t0),(0,1), 'reflect')-dt)/dt
                mute = kwargs['smute']
                filter = [(stretch >0.0) & ( stretch < mute)]
                 #interpolate
                result[i]['trace'] = np.interp(tx, t0, trace['trace']) * filter
                
        return result



def nmo(dataset, **kwargs):   
        dataset.sort(order='cdp')
        cdps = np.unique(dataset['cdp'])
        minCdp = cdps[0]
        times = kwargs['times']
        dt = kwargs['dt'] 
        ns = kwargs['ns']
        nt = dataset.shape[0]
        traces = np.arange(nt)
        
        cdp_columns = dataset['cdp'] - minCdp
        vels = np.zeros_like(dataset['trace'])
        
        for i in range(cdp_columns.size):
                vels[i] = kwargs['vels'][cdp_columns[i]]
        
        tx = np.ones(dataset['trace'].shape) * times
        offset = dataset['offset'][:, None]
        t0 = _nmo_calc(tx, vels, offset)
        t0 = np.nan_to_num(t0)
        
        shifts = np.ones(dataset['trace'].shape) * (ns * dt * traces[:, None])
        tx += shifts
        t0 += shifts
        
        result = np.interp(tx.ravel(), t0.ravel(), dataset['trace'].flatten()) 
        dataset['trace'] = result.reshape(nt, ns)

        #calculate stretch between each sample
        
        stretch = 100.0*(np.abs(t0 - np.roll(t0, 1, axis=-1))/dt)
        stretch = np.nan_to_num(stretch)
        mute = kwargs['smute'] * 1.0
        filter = [(stretch >0.0) & ( stretch < mute)][0]
        dataset['trace'] *= filter
        return dataset 


def axis_nmo(dataset, **kwargs):   
        pass

              

def _stack_gather(gather):
        '''stacks a single gather into a trace.
        uses header of first trace. normalises
        by the number of nonzero samples'''
        pilot = gather[np.argmin(gather['offset'])]
        norm = gather['trace'].copy()
        norm = np.nan_to_num(norm)
        norm = norm **0
        norm = np.sum(norm, axis=-2)
        pilot['trace'] = np.sum(gather['trace'], axis=-2)/norm
        return pilot

        
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
                if e.button == 1:
                        print "(%.1f, %.3f)," %(e.xdata, e.ydata), 
                        w = np.abs(np.diff(ax.get_xlim())[0])/50.
                        h = np.abs(np.diff(ax.get_ylim())[0])/50.
                        circ= patches.Ellipse((e.xdata, e.ydata), width=w, height=h,  fc='k')
                        ax.add_patch(circ)
                        dr = DraggablePoint(circ)
                        dr.connect()
                        drs.append(dr)  
                        fig.canvas.draw()

        vels = kwargs['velocities']
        nvels = vels.size
        ns = kwargs['ns']
        result = np.zeros((nvels,ns),'f')
        loc = np.mean(workspace['cdp'])
        for v in range(nvels):
                panel = workspace.copy()
                kwargs['vels'] = np.ones(kwargs['ns'], 'f') * vels[v]
                panel = nmo(panel, None, **kwargs)
                norm = panel['trace'].copy()
                norm[np.nonzero(norm)] = 1
                n = np.sum(norm, axis=0)
                
                a  = np.sum(panel['trace'], axis=0)**2
                b = n * np.sum(panel['trace']**2, axis=0)
                
                window = kwargs['smoother']*1.0
                kernel = np.ones(window)/window
                a = np.convolve(a, kernel, mode='same')
                b = np.convolve(b, kernel, mode='same')

                result[v:] = np.sqrt(a/b)
        
        pylab.imshow(result.T, aspect='auto', extent=(min(vels), max(vels),kwargs['ns']*kwargs['dt'],0.), cmap='jet')
        pylab.xlabel('velocity')
        pylab.ylabel('time')
        pylab.title("cdp = %d" %np.unique(loc)) 
        pylab.colorbar()
        print "vels[%d]=" %loc,
        fig = pylab.gcf()
        ax = fig.gca()
        fig.canvas.mpl_connect('button_press_event', onclick)
        drs = []
        
        
        pylab.show()
        print ''
        print "vels[%d]=" %loc, 
        for dr in drs:
                print "(%.1f, %.3f)," %dr.point.center,
                


def _lmo_calc(aoffset, velocity):
        t0 = -1.0*aoffset/velocity
        return t0
        

def lmo(dataset, **kwargs):
        offsets = np.unique(dataset['offset'])
        for offset in offsets:
                aoffset = np.abs(offset)
                shift = _lmo_calc(aoffset, kwargs['lmo'])
                shift  = (shift*1000).astype(np.int)
                inds= [dataset['offset'] == offset]
                dataset['trace'][inds] =  np.roll(dataset['trace'][inds], shift, axis=-1) #results[inds]
        return dataset



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


def bandpass(dataset, **kwargs):
        
        # Sample rate and desired cutoff frequencies (in Hz).
        fs = 1./kwargs['dt']
        lowcut = kwargs['lowcut']
        highcut = kwargs['highcut']
            
        dataset['trace'] = butter_bandpass_filter(np.fliplr(dataset['trace']), lowcut, highcut, fs, order=3)
        dataset['trace'] = butter_bandpass_filter(np.fliplr(dataset['trace']), lowcut, highcut, fs, order=3)
        return dataset
        

def fk_view(dataset, **kwargs):
        mid= dataset.size/2
        f = np.abs(np.fft.rfft2(dataset['trace']))
        freq = np.fft.rfftfreq(kwargs['ns'], d=kwargs['dt'])
        k = np.fft.rfftfreq(dataset.size, d=kwargs['dx'])
        kmax = k[-1]
        f[:mid] = f[:mid][::-1]
        f[mid:] = f[mid:][::-1]
        pylab.figure()
        pylab.imshow(f.T, aspect='auto', extent=[-1*kmax, kmax, freq[-1], freq[0]])
        pylab.colorbar()

        
def fk_design(dataset, **kwargs):
        mid= dataset.size/2
        f = np.abs(np.fft.rfft2(dataset['trace']))
        freq = np.fft.rfftfreq(kwargs['ns'], d=kwargs['dt'])
        k = np.fft.rfftfreq(dataset.size, d=kwargs['dx'])       
        k = k[:-1]
        kmax = k[-1]
        k_axis = np.hstack([k, k[::-1]])[:, None]

        
        column, row = np.indices(f.shape)
        row = row.astype(np.float)
        column = column.astype(np.float)    
        column.fill(1.0)
        row.fill(1.0)
        row *= freq
        column *= k_axis
        m = row/column
        m[:mid] = m[:mid][::-1]
        m[mid:] = m[mid:][::-1]
        mask = m > kwargs['fkVelocity'] 
        m[mask] = 1
        m[~mask] = 0
        window = kwargs['fkSmooth'] 
        vec= np.ones(window)/(window *1.0)
        smoothed_m = np.apply_along_axis(lambda m: np.convolve(m, vec, mode='valid'), axis=-1, arr=m)
        valid = smoothed_m.shape[-1]
        m[:, :valid] = smoothed_m
        pylab.figure()
        pylab.imshow(m.T, aspect='auto', extent=[-1*kmax, kmax, freq[-1], freq[0]])
        pylab.colorbar()
        z = m.copy()
        z[:mid] = z[:mid][::-1]
        z[mid:] = z[mid:][::-1]
        return z

        
def fk_filter(dataset, **kwargs):
        for s in np.unique(dataset['fldr']):
                shot = dataset['trace'][dataset['fldr'] == s]
                filter = kwargs['fkFilter']
                nt = shot.shape[0]
                delta = abs(nt - filter.shape[0])
                if  delta > 0:
                        shot = np.vstack([shot, np.zeros_like(shot[:delta])])
                f = np.fft.rfft2(shot)
                
                result = np.fft.irfft2(f*filter)[:nt]
                dataset['trace'] [dataset['fldr'] == s]= 0.0
                dataset['trace'] [dataset['fldr'] == s]= result
        return dataset

        
def trim(dataset, **kwargs):
        dataset['tstat'] = 0
        model = kwargs['model']
        cdps = np.unique(model['cdp'])
        start, end = (kwargs['gate'] /kwargs['dt']).astype(np.int)
        centre = kwargs['ns']/2
        m = kwargs['maxshift']
        for cdp in cdps:
                gather = dataset[dataset['cdp'] == cdp].copy()
                gather['trace'][:,:start] = 0
                gather['trace'][:,end:] = 0
                
                pilot = model['trace'][model['cdp'] == cdp].ravel()
                pilot[:start] = 0
                pilot[end:] = 0		
                
                result = np.apply_along_axis(lambda m: np.correlate(m, pilot, mode='same'), axis=-1, arr=gather['trace'])
                result[:,:centre-m] = 0
                result[:,centre+m+1:] = 0
                
                peaks = np.argmax(np.abs(result), axis=-1)
                dataset['tstat'][dataset['cdp'] == cdp] = peaks
        
        dataset['tstat'] -= centre.astype(np.int16)     
        dataset['tstat'] *= -1
        return dataset
        


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
    
    