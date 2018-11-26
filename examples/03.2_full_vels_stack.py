import toolbox
import numpy as np
import pylab

#initialise
data, params = toolbox.initialise('prepro.su')

#load vels
params['vels'] = np.fromfile('vels_full.bin').reshape(-1, params['ns'])
params['smute'] = 200

#normal moveout correction
nmo = toolbox.nmo(data, None, **params)

#AGC
toolbox.agc(nmo, None, **params)
#stack
stack = toolbox.stack(nmo, None, **params)
params['gamma'] = -1
toolbox.tar(stack, None, **params)
stack.tofile("field_stack2.su")

params['primary'] = None
params['secondary'] = 'cdp'
toolbox.display(stack, **params)
pylab.show()