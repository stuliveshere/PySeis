import toolbox
import numpy as np
import pylab

data, params = toolbox.initialise('prepro.su')

cdps = np.unique(data['cdp'])

#recreate original velocity field
#~ vels = {}
#~ vels[753]= (2456.0, 0.153), (2772.1, 0.413), (3003.2, 0.612), (3076.1, 0.704), (3270.7, 1.056), (3367.9, 1.668), (3538.2, 2.204), (3671.9, 3.566), (3915.1, 5.908), 
#~ vels[3056]=(2456.0, 0.153), (2772.1, 0.413), (3003.2, 0.612), (3076.1, 0.704), (3270.7, 1.056), (3367.9, 1.668), (3538.2, 2.204), (3671.9, 3.566), (3915.1, 5.908), 
#~ params['cdp'] = cdps
#~ params['vels'] = toolbox.build_vels(vels, **params)
#~ np.array(params['vels']).tofile('vels_initial.bin')


params['vels'] = np.fromfile('vels_initial.bin').reshape(-1, params['ns'])
#~ pylab.imshow(params['vels'].T, aspect='auto')
#~ pylab.colorbar()
#~ pylab.show()

#agc and stack
toolbox.agc(data, None, **params)
params['smute'] = 200
toolbox.nmo(data, None, **params)
stack = toolbox.stack(data, None, **params)
params['gamma'] = -1
toolbox.tar(stack, None, **params)
stack.tofile('field_stack.su')
#display
params['primary'] = None
params['secondary'] = 'cdp'
toolbox.display(stack, **params)
pylab.show()
