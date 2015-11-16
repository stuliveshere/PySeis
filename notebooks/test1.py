import numpy as np
from matplotlib import collections
import toolbox
dmap = np.memmap(file, dtype=toolbox.typeSU(1501), mode='r')
eps = np.unique(dmap['ep'])
for ep in eps[:1]:
    panel = dmap[dmap['ep'] == ep].copy()
    panel = toolbox.agc(panel, None, **params)

    trace_centers = np.linspace(1,284, panel.size).reshape(-1,1)
    scalar = 284/(panel.size*0.5)
    panel['trace'][:,-1] = np.nan
    x = panel['trace'].ravel()
    x[x < 0] = 0
    y = np.meshgrid(np.arange(1501), np.arange(284))[0].ravel() 
    
    zero_crossings = np.where(x == 0)[0]+1
    zero_crossings = zero_crossings[np.diff(zero_crossings) == 1]
    #zero_crossings = np.where(np.diff(np.signbit(x)))[0]+1
    
    x = ((panel['trace']*scalar)+trace_centers).ravel()

    xverts = np.split(x, zero_crossings)
    yverts = np.split(y, zero_crossings)
    
    
    polygons = [zip(xverts[i], yverts[i]) for i in range(0, len(xverts)) if len(xverts[i]) > 2]
    
    xlines = np.split(x, 284)
    ylines = np.split(y, 284)
    lines = [zip(xlines[a],ylines[a]) for a in range(len(xlines))]  


    fig = pylab.figure()
    ax = fig.add_subplot(111)
    col = collections.PolyCollection(polygons)
    col.set_color('k')
    ax.add_collection(col, autolim=True)
    col1 = collections.LineCollection(lines)
    col1.set_color('k')
    ax.add_collection(col1, autolim=True)
    ax.autoscale_view()
    pylab.xlim([0,284])
    pylab.ylim([0,1500])
    ax.set_ylim(ax.get_ylim()[::-1])
    pylab.tight_layout()
    pylab.show(block=false)