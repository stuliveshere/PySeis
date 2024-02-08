import toolbox
import numpy as np
import pylab

#extract shot record
data, params = toolbox.initialise("prepro.su")
mask = data['fldr'] == 221
shot = data[mask].copy()

#agc
toolbox.agc(shot, None, **params)
params['primary'] = 'fldr'
params['secondary'] = 'tracf'
params['wiggle'] = True
toolbox.display(shot, **params)

#fk plot
params['dx'] = 33.5 #m
#~ toolbox.fk_view(shot,  **params)


#~ #fk filter design
params['fkVelocity'] = 2000
params['fkSmooth'] = 20
params['fkFilter'] = toolbox.fk_design(shot, **params) 
shot = toolbox.fk_filter(shot, None, **params)
toolbox.display(shot, **params)

##############end of testing
#~ data, nparams = toolbox.initialise("prepro.su")

#~ toolbox.agc(data, None, **params)
#~ data = toolbox.fk_filter(data, None, **params)
#~ #nmo
#~ params['vels'] = np.fromfile('vels_full.bin').reshape(-1, params['ns'])
#~ params['smute'] = 150
#~ toolbox.nmo(data, None, **params)
#~ data.tofile("fk_nmo_gathers.su")
#~ toolbox.agc(data, None, **params)
#~ #stack
#~ stack = toolbox.stack(data, None, **params)
#~ params['gamma'] = -1
#~ toolbox.tar(stack, None, **params)
#~ stack.tofile("fk_stack.su")
#~ #display
#~ params['primary'] = None
#~ params['secondary'] = 'cdp'
#~ toolbox.display(stack, **params)


pylab.show()

