import PySeis as ps
import numpy as np
import pylab

#import dataset
input = ps.core.su.SU("./data/sample.su")
input.read("./data/raw.npy")

#initialise dataset
#~ data, params = toolbox.initialise("geometries.su")

#trim data
#~ params['ns'] = 1500
#~ data = toolbox.slice(data, None, **params)
#~ data.tofile("geom_short.su")

#initialise dataset
#data, params = toolbox.initialise("geom_short.su")

#agc
#~ toolbox.agc(data, None, **params)

#params['gamma'] = 1.5
#toolbox.tar(data, None, **params)

#kills = [270, 300, 374, 614] #fldr

#mask = toolbox.build_mask(data['fldr'], kills)

#data = data[mask]
#data.tofile("prepro.su")

#display
#~ params['primary'] = 'fldr'
#~ params['secondary'] = 'tracf'
#~ params['wiggle'] = True
#~ toolbox.display(data, **params)

#~ pylab.show()


