import toolbox
import numpy as np
import pylab

data, params = toolbox.initialise('prepro.su')

#moveout
params['vels'] = np.fromfile('vels_initial.bin').reshape(-1, params['ns'])
params['smute'] = 200
toolbox.nmo(data, None, **params)
#agc and stack
toolbox.agc(data, None, **params)
stack = toolbox.stack(data, None, **params)
#amplitude adjustment
params['gamma'] = -1
toolbox.tar(stack, None, **params)
#stack.tofile('field_stack.su')
#display
params['primary'] = None
params['secondary'] = 'cdp'
toolbox.display(stack, **params)
pylab.show()
