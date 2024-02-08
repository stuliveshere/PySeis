'''
displays multiple stacks
'''
import toolbox
import pylab
import numpy as np

filelist = ["1st_vels_stack.su", 
#"1st_vels_stack_elev.su", 
"fk_stack.su", 
#"model.su", 
"model_filtered.su", 
#"trim_stack.su",
"trim_stack2.su",
]

dataset, params = toolbox.initialise(filelist[0])
dataset['fldr'] = 0
for index, file in enumerate(filelist[1:]):
	data, junk = toolbox.initialise(file)
	data['fldr'] = index + 1
	dataset = np.column_stack([dataset, data])

params['window'] = 1000
toolbox.agc(dataset, None, **params)
params['primary'] = 'fldr'
params['secondary'] = 'cdp'
params['clip'] = 0.02
toolbox.display(dataset, **params)
pylab.show()
	
