


import toolbox
import numpy as np
from matplotlib import collections
from timeit import Timer
import pylab

def func(panel): 
    
    panel['trace'][:,-1] = np.nan
    trace_centers = np.linspace(1,284, panel.size).reshape(-1,1)
    scalar = 284/(panel.size*0.1)
    y = np.meshgrid(np.arange(1501), np.arange(284))[0].ravel() 
    offsets = (np.meshgrid(np.arange(1501), np.arange(284))[1]+1).ravel()
    x = ((panel['trace']*scalar)+trace_centers).ravel()
    xlines = np.split(x, 284)
    ylines = np.split(y, 284)
    lines = [zip(xlines[a],ylines[a]) for a in range(len(xlines))]  
    fig,ax = pylab.subplots()
    ax.fill_betweenx(y,offsets,x,where=(x>offsets),color='k')
    col1 = collections.LineCollection(lines)
    col1.set_color('k')
    ax.add_collection(col1, autolim=True)
    pylab.xlim([0,284])
    pylab.ylim([0,1500])
    ax.set_ylim(ax.get_ylim()[::-1])
    pylab.tight_layout()
    pylab.show()

file = "/home/sfletcher/Downloads/2d_land_data/2D_Land_data_2ms/Line_001.su"
data, params = toolbox.initialise(file)
dmap = np.memmap(file, dtype=toolbox.typeSU(1501), mode='r')
eps = np.unique(dmap['ep'])
for ep in eps[:1]:
    params['window'] = 500
    panel = dmap[dmap['ep'] == ep].copy()
    panel = toolbox.agc(panel, None, **params)
    func(panel)
    #t = Timer("""func(panel)""", setup="from __main__ import func; from __main__ import panel")
    #print t.timeit(100)


#777.01802206