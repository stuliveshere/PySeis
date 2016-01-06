import PySeis.display.wiggle as plot
import toolbox
import pylab
import numpy as np

def _2d(func):
	'''decorator to apply along axis'''
	def wrapped(*args, **kwargs):
		return np.apply_along_axis(func, axis=-1, arr=args[0],  **kwargs)
	return wrapped

@_2d
def window_rms(arr=None, window_size=100):
	a2 = np.power(arr,2)
	window = np.ones(window_size)/float(window_size)
	return np.sqrt(np.convolve(a2, window, 'valid'))

@_2d	
def scale(dataset):
	dataset['trace'] /= np.amax(np.abs(dataset['trace']))

if __name__ == "__main__":

	file = "/home/sfletcher/Downloads/2d_land_data/2D_Land_data_2ms/Line_001.su"

	data = toolbox.read(file)
	
	data = data[data['tracf'] > 0]
	
	toolbox.scan(data)

	ffids =  np.unique(data['fldr'])
	
	
	parms = {}
	
	parms['dt'] = data['dt'][0]

	for shot in ffids:
		panel =  data[data['fldr'] == shot]
		#print shot
		
		parms["primary"] = 'fldr'
		parms["step"] = 1
		parms["window"] = 1000
		
		#toolbox.display(panel, None, **parms)
		
		parms['lowcut'] = 5
		parms['highcut'] = 200
		parms['dt'] = 0.001
		
		#~ toolbox.agc(panel, None, **parms)
		
		panel['trace'][:,:-99] = window_rms(panel['trace'], 50)
		
		panel['trace'][:,:-1] = np.diff(panel['trace'], n=1)
		
		
		panel['trace'][:,:15] = 0
		panel['trace'][:,1000:] = 0
		
		panel = scale(panel)
		
		#toolbox.bandpass(panel, None, **parms)
		#~ toolbox.agc(panel, None, **parms)
		plot(panel)
		#~ pylab.figure()
		#~ pylab.imshow(drms.T, aspect='auto')
		
		pylab.show()
		

