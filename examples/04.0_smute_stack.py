import toolbox
import numpy as np
import pylab


#~ for mute in range(110,200, 10):
#initialise
data, params = toolbox.initialise('prepro.su')

#load vels
params['vels'] = np.fromfile('vels_full.bin').reshape(-1, params['ns'])

params['smute'] = 150 #mute

#normal moveout correction
toolbox.nmo(data, None, **params)

#AGC
toolbox.agc(data, None, **params)
#stack
stack = toolbox.stack(data, None, **params)
params['gamma'] = -1
toolbox.tar(stack, None, **params)
data['tstat'] /= 2
toolbox.apply_statics(stack, None, **params)
#~ stack.tofile("smute_%d.su" %mute)
stack.tofile("1st_vels_stack_elev.su")	
# i think I like 150

