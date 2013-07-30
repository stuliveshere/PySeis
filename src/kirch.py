compile = 0
if compile:
	f_code =open('source.f90', 'r').read()
	import numpy.f2py as f2py
	f2py.compile(f_code, 
				modulename='f' , 
				verbose=0)	

import f
import numpy as np
import su
from mpi4py import MPI
import sys
from ConfigParser import SafeConfigParser as ini

def median(panel, window=50):
	smoother  = np.ones(window)/float(window)
	holder = np.zeros_like(panel)
	for i in range(ns):
		slice =panel[:,i]
		wrap = np.hstack((slice[::-1], slice, slice[::-1]))
		smooth = np.convolve(wrap, smoother, mode='same')
		holder[:,i] = smooth[len(slice): -len(slice)]
	return panel - holder

def rho(trace, dt):
	fft = np.fft.rfft(trace) #up to the nyquist
	freq = np.abs(np.fft.fftfreq(fft.shape[-1], dt)) #force nyquest to positive value

	mag = np.abs(fft)  #magnitude spectrum
	phase = np.angle(fft) #phase spectrum

	phasenew = np.zeros_like(phase, dtype=np.complex)
	phasenew.imag = phase + np.radians(45)
	mag *= np.sqrt(freq) #scale

	z = mag*np.exp(phasenew) #build new complex spectrum
	z.imag[-1] = 0.0
	return np.fft.irfft(z) #includes hermitian conjugate

def halfint_init(ns, dt, rho=None):
	n = ns
	if rho == None:
		rho = 1.0+1.0/n
	nw = n/2+1
	freq = np.fft.fftfreq(nw, dt)
	i = np.arange(nw)
	om = -2.*np.pi*i/n
	
	cw = np.zeros_like(freq, dtype=complex)
	cw.real = np.cos(om)
	cw.imag = np.sin(om)

	cz = np.zeros_like(freq, dtype=complex)
	cz.real = 1.-rho*cw.real
	cz.imag = -rho*cw.imag
	cz = np.sqrt(cz)

	cf = np.zeros_like(freq, dtype=complex)
	cf.real = cz.real
	cf.imag = cz.imag/n
	return cf
	
def halfint(trace, cf): #adj=1
	cx = np.fft.rfft(trace, axis=-1)
	cx.real *= cf.real
	cx.imag *= cf.imag
	return np.fft.irfft(cx, axis=-1)
	
def warn(comment):
	#~ if rank == 0 and verbose == 1:
	sys.stderr.write(comment)


par = ini()
par.read(sys.argv[1])

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

verbose = par.getint('other', 'verbose')

if rank == 0:
	data = su.readSU(par.get('files', 'infile'))
else: 
	data = None
	
data = comm.bcast(data, root=0)


#set up some constants
ap = np.tan(np.radians(par.getfloat('other', 'dip')))
dt = data['dt'][0]*1e-6
dx = par.getfloat('other', 'dx')
ns = data['ns'][0]
nt = data.shape[0]
fnyq = 1.0/(2.0*dt)
traveltimes = np.arange(ns)*dt+dt
offsets = np.unique(data['offset'])


#read in vels
velfile= par.get('files', 'velfile')
vels = np.fromfile(velfile, dtype=np.float32).reshape(-1, ns)

#set up  filtering flags
antialiasing= par.getint('filters', 'antialiasing')
rhofilter = par.getint('filters', 'rhofilter')
medianfilter= par.getint('filters', 'medianfilter')

for offset in offsets:

	input = data[data['offset'] == offset]
	
	if (medianfilter == 1) and (input['trace'].shape[0] > 50):
		input['trace'] = median(input['trace'], 50)
	
	if rhofilter == 1: input['trace'] = rho(input['trace'], dt)
	
	if antialiasing ==1:
		intpanel = np.cumsum(input['trace'], axis=1)
		intpanel =np.fliplr(intpanel)
		intpanel= np.cumsum(intpanel, axis=1)#double integration (for anti-aliasing)
		intpanel =np.fliplr(intpanel)
	else:
		intpanel = input['trace']
	
	h = offset/2.0 #half offset
	cdps = (input['sx'] + input['gx'])/2.0
	cdpn = input['cdp']-1

	if rank == 0:
		indexes = np.array_split(np.arange(cdps.size), size)
	else:
		indexes= 0
		
	indexes = comm.scatter(indexes, root=0)
	
	output = np.zeros_like(input['trace'], dtype=np.float64)
	fold = np.ones_like(output)
	
	#generate lookup dictionaries
	keys = sorted(np.unique(cdps)) #cdpx
	values = range(1,len(keys)+1) #cdpn
	d = dict(zip(keys, values)) #cdpx : cdpn
	r_d = dict(zip(values, keys)) #cdpn: cdpx
	ncdps = cdps.size
	

	for index in indexes: #loop over  cdps
		cdp = cdps[index]
		warn('rank(%d) offset(%d) cdpn(%d) cdpx(%f)\n' %(rank, offset, cdpn[index], cdp))

		for sample, t0 in enumerate(traveltimes):
			v = vels[cdpn[index],  sample]  
			xwidth=ap*v*t0/2.0 # rough half aperture calculation. 
			low = cdp-xwidth
			high = cdp+xwidth
			mask = (cdps > low) & (cdps < high)
			
			aperture =  cdps[mask]
			x = aperture - cdp
			ts, tr = f.traveltime(t0,x,h,v)

			t = ts + tr
			mask = (t <  ns*dt-dt)
			aperture = aperture[mask]
			
			if aperture.size > 0:

				aperture = np.array([d[key] for key in aperture])-1
				t = t[mask]
				tr = tr[mask]
				ts = ts[mask]
				x = x[mask]
				g = f.geoms(t,v)
				obliq = t0/t #approximate weights from Bancroft, 2002
	
				
				if antialiasing == 1 :
					z = np.zeros_like(aperture, dtype=np.float)
					steps = z.size
					tx = np.abs(x-h)/(v*v*(tr+dt))+ np.abs(x+h)/(v*v*(ts+dt))
					
					for slice in range(steps):
						ti = t[slice]
						deltat = np.abs(tx[slice]*dx)
						trace = intpanel[aperture[slice].astype(np.int)]
						z[slice] = f.pick(ti,deltat,trace,dt,0.0)							
				else:
					t /= dt
					t_high = np.ceil(t).astype(np.int)
					t_low = t_high - 1
					scale_high = 1.0 - (t_high -  t)
					scale_low = 1.0 - scale_high
					z_high = intpanel[aperture.astype(np.int), t_high]*scale_high
					z_low = intpanel[aperture.astype(np.int), t_low]*scale_low
					z = z_high + z_low

				window = np.ones_like(t, dtype=np.float)
				
				if window.size > 5: #taper ends of aperture
					taper = np.hanning(np.floor(t.size/3.))
					ind = np.argmax(taper)
					slice = taper[:taper.size/2]
					window[:len(slice)] *= slice
					window[-1*len(slice):] *= slice[::-1]
				
				summation = np.sum(z*obliq*g*window)
			
				output[index,sample] += summation
				fold[index,sample] += z.size
			
	

	output /= fold
	comm.Barrier()
	if rank != 0:
		comm.Send(output, dest=0)

	if rank == 0:
		result = output.copy()
		for worker in range(1, size):
			comm.Recv(output, source=worker)
			result += output

		input['trace'] = result
		data[data['offset'] == offset] = input

if rank == 0:
	su.writeSU(data, par.get('files', 'outfile'))		

		



