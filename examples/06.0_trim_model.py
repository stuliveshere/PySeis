import toolbox
import numpy as np
import pylab


stack,  params = toolbox.initialise("fk_stack.su")

stack['fldr'] = 1
params['dx'] = 33.5/2.0 #m
params['fkVelocity'] = 6000
params['fkSmooth'] = 20
params['fkFilter'] = toolbox.fk_design(stack, **params) 
stack = toolbox.fk_filter(stack, None, **params)


#bandpass
params['lowcut'] = 10.0
params['highcut'] = 100.0
toolbox.bandpass(stack, None, **params)

stack.tofile("model_filtered.su")

#display
#~ params['primary'] = None
#~ params['secondary'] = 'cdp'
#~ toolbox.display(stack, **params)
#~ pylab.show()

