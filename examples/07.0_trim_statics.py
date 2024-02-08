import toolbox
import pylab
import numpy as np

model, mparams = toolbox.initialise("model_filtered.su")

gathers, params = toolbox.initialise("fk_nmo_gathers.su")
params['model'] = model
params['gate'] = (.4, 1.0) #seconds
params['maxshift'] = 4 #samples
toolbox.trim(gathers, None, **params)


toolbox.apply_statics(gathers, None, **params)
stack = toolbox.stack(gathers, None, **params)
params['gamma'] = -1
toolbox.tar(stack, None, **params)
stack.tofile("trim_stack2.su")

