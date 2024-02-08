import numpy as np
import matplotlib.pyplot as pylab
from matplotlib.widgets import Slider




#==================================================
#                                 decorators
#==================================================


def io(func):
        '''
        an io decorator that allows
        input/output to be either a filename 
        (i.e. a string) or an array
        '''
        def wrapped(*args, **kwargs) :
                if type(args[0]) == type(''):
                        workspace = read(args[0])
                else:
                        workspace = args[0]
                result = func(workspace, **kwargs)
                if type(result) != type(None):
                        if type(args[1]) == type(''):
                                return write(result, args[1])
                        else:
                                return result
        return wrapped

#==================================================
#                                 display tools
#==================================================


class KeyHandler(object):
        def __init__(self, fig, ax, dataset, kwargs):
                self.fig = fig
                self.ax = ax
                self.kwargs = kwargs
                self.dataset = dataset 
                self.start = 0
                if kwargs['primary'] == None:
                        self.slice = self.dataset
                else:
                        keys = np.unique(dataset[kwargs['primary']])
                        self.keys = keys[::kwargs['step']]
                        self.nkeys = self.keys.size
                        self.ensemble()
                
                if 'clip' in kwargs and kwargs['clip'] != 0:
                        self.clip = kwargs['clip']
                else:
                        self.clip = np.mean(np.abs(self.dataset['trace']))
                        
                print 'PySeis Seismic Viewer'
                print 'type "h" for help'
                self.draw()
                
        def __call__(self, e):
                print e.xdata, e.ydata
                if e.key == "right":
                        self.start += 1
                        self.ensemble()
                elif e.key == "left":
                        self.start -= 1
                        self.ensemble()
                elif e.key == "up":
                        self.clip /= 1.1
                        print self.clip
                elif e.key == "down":
                        self.clip *= 1.1
                        print self.clip
                elif e.key == "h":
                        print "right arrow: next gather"
                        print "left arrow: last gather"
                        print "up arrow: hotter"
                        print "down arrow: colder"
                        print "clip=", self.clip
                        
                else:
                        return
                self.draw()
                      
                
        def draw(self):
                self.ax.cla()
                self.im = self.ax.imshow(self.slice['trace'].T, aspect='auto', cmap='Greys', vmax =self.clip, vmin=-1*self.clip)
                try:
                        self.ax.set_title('%s = %d' %(self.kwargs['primary'], self.keys[self.start]))
                except AttributeError:
                        pass
                self.fig.canvas.draw()      

        def ensemble(self):
                try:
                        self.slice = self.dataset[self.dataset[self.kwargs['primary']] == self.keys[self.start]]
                except IndexError:
                        self.start = 0


@io	
def display(dataset, **kwargs):
        '''
        iterates through dataset using
        left and right keys
        parameters required:
                primary key
                seconary key
                step size
                
        works well unless you want to load a big dataset...
        '''
        fig = pylab.figure()
        ax = fig.add_subplot(111)
        eventManager =  KeyHandler(fig, ax, dataset, kwargs)
        fig.canvas.mpl_connect('key_press_event',eventManager)

        
def scan(dataset):
        print "    %0-35s: %0-15s   %s" %('key', 'min', 'max')
        print "========================================="
        for key in np.result_type(dataset).descr:
                a = np.amin(dataset[key[0]])
                b = np.amax(dataset[key[0]])
                if (a != 0) and (b != 0):
                        print "%0-35s %0-15.3f  %.3f" %(key, a, b)
        print "========================================="	
                

#~ def build_vels(times, velocities, ns=1000, dt=0.001):
        #~ '''builds a full velocity trace from a list of vels and times'''
        #~ tx = np.linspace(dt, dt*ns, ns)
        #~ vels = np.interp(tx, times, velocities)
        #~ vels = np.pad(vels, (100,100), 'reflect')
        #~ vels = np.convolve(np.ones(100.0)/100.0, vels, mode='same')
        #~ vels = vels[100:-100]
        #~ return vels
        
                
       
@io
def cp(workspace, **params):
        return workspace

@io
def agc(workspace, window=100, **params):
        '''
        automatic gain control
        inputs:
        window
        '''
        vec = np.ones(window, 'f')
        func = np.apply_along_axis(lambda m: np.convolve(np.abs(m), vec, mode='same'), axis=-1, arr=workspace['trace'])
        workspace['trace'] /= func
        workspace['trace'][~np.isfinite(workspace['trace'])] = 0
        workspace['trace'] /= np.amax(np.abs(workspace['trace']))
        return workspace
        
def ricker(f, length=0.512, dt=0.001):
    t = np.linspace(-length/2, (length-dt)/2, length/dt)
    y = (1.0 - 2.0*(np.pi**2)*(f**2)*(t**2)) * np.exp(-(np.pi**2)*(f**2)*(t**2))
    y = np.around(y, 10)
    inds = np.nonzero(y)[0]
    return y[np.amin(inds):np.amax(inds)]
 
 
def conv(workspace, wavelet):
        workspace['trace'] = np.apply_along_axis(lambda m: np.convolve(m, wavelet, mode='same'), axis=-1, arr=workspace['trace'])
        return workspace
@io
def fx(workspace, **params):
        f = np.abs(np.fft.rfft(workspace['trace'], axis=-1))
        correction = np.mean(np.abs(f), axis=-1).reshape(-1,1)
        f /= correction
        f = 20.0*np.log10(f)[:,::-1]
        
        freq = np.fft.rfftfreq(params['ns'], params['dt'])
        print params['ns'], params['dt']
        
        hmin = np.amin(workspace['cdp'])
        hmax = np.amax(workspace['cdp'])
        vmin = np.amin(freq)
        vmax = np.amax(freq)
        extent=[hmin,hmax,vmin,vmax]
        pylab.imshow(f.T, aspect='auto', extent=extent)


def db(data):
        return 20.0*np.log10(data)

        
import numpy as np
su_header_dtype = np.dtype([
('tracl', np.int32),
('tracr', np.int32),
('fldr', np.int32),
('tracf', np.int32),
('ep', np.int32),
('cdp', np.int32),
('cdpt', np.int32),
('trid', np.int16),
('nvs', np.int16),
('nhs', np.int16),
('duse', np.int16),
('offset', np.int32),
('gelev', np.int32),
('selev', np.int32),
('sdepth', np.int32),
('gdel', np.int32),
('sdel', np.int32),
('swdep', np.int32),
('gwdep', np.int32),
('scalel', np.int16),
('scalco', np.int16),
('sx', np.int32),
('sy', np.int32),
('gx', np.int32),
('gy', np.int32),
('counit', np.int16),
('wevel', np.int16),
('swevel', np.int16),
('sut', np.int16),
('gut', np.int16),
('sstat', np.int16),
('gstat', np.int16),
('tstat', np.int16),
('laga', np.int16),
('lagb', np.int16),
('delrt', np.int16),
('muts', np.int16),
('mute', np.int16),
('ns', np.uint16),
('dt', np.uint16),
('gain', np.int16),
('igc', np.int16),
('igi', np.int16),
('corr', np.int16),
('sfs', np.int16),
('sfe', np.int16),
('slen', np.int16),
('styp', np.int16),
('stas', np.int16),
('stae', np.int16),
('tatyp', np.int16),
('afilf', np.int16),
('afils', np.int16),
('nofilf', np.int16),
('nofils', np.int16),
('lcf', np.int16),
('hcf', np.int16),
('lcs', np.int16),
('hcs', np.int16),
('year', np.int16),
('day', np.int16),
('hour', np.int16),
('minute', np.int16),
('sec', np.int16),
('timebas', np.int16),
('trwf', np.int16),
('grnors', np.int16),
('grnofr', np.int16),
('grnlof', np.int16),
('gaps', np.int16),
('otrav', np.int16), #179,180
('d1', np.float32), #181,184
('f1', np.float32), #185,188
('d2', np.float32), #189,192
('f2', np.float32), #193, 196
('ShotPoint', np.int32), #197,200
('unscale', np.int16), #201, 204
('TraceValueMeasurementUnit', np.int16),
('TransductionConstantMantissa', np.int32),
('TransductionConstantPower', np.int16),
('TransductionUnit', np.int16),
('TraceIdentifier', np.int16),
('ScalarTraceHeader', np.int16),
('SourceType', np.int16),
('SourceEnergyDirectionMantissa', np.int32),
('SourceEnergyDirectionExponent', np.int16),
('SourceMeasurementMantissa', np.int32),
('SourceMeasurementExponent', np.int16),
('SourceMeasurementUnit', np.int16),
('UnassignedInt1', np.int32),
('ns1', np.int32),
])


def typeSU(ns):
        return np.dtype(su_header_dtype.descr + [('trace', ('<f4',ns))])
        
                
def readSUheader(filename):
        raw = open(filename, 'rb').read()
        return np.fromstring(raw, dtype=su_header_dtype, count=1)

def read(filename=None):
        if filename == None:
                raw= sys.stdin.read()
        else:
                raw = open(filename, 'rb').read()
        return readData(raw)
        
def readData(raw):
        su_header = np.fromstring(raw, dtype=su_header_dtype, count=1)
        ns = su_header['ns'][0]
        file_dtype = typeSU(ns)
        data = np.fromstring(raw, dtype=file_dtype)
        return data	
        
def write(data, filename=None):
        if filename == None:
                data.tofile(sys.stdout)
        else:
                data.tofile(filename)
                





