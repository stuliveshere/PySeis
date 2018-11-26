import toolbox
import numpy as np
import pylab

data, params = toolbox.initialise('field_stack.su')

toolbox.fx(data, None, **params)
pylab.show()