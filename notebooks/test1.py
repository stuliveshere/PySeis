import numpy as np
from matplotlib import collections
import toolbox
import pylab

file = "/home/sfletcher/Downloads/2d_land_data/2D_Land_data_2ms/Line_001.su"
data, params = toolbox.initialise(file)
dmap = data #np.memmap(file, dtype=toolbox.typeSU(1501), mode='r')
eps = np.unique(dmap['ep'])
for ep in eps[:1]:
    params['window'] = 500
    panel = dmap[dmap['ep'] == ep].copy()
    print 'doing agc'
    panel = toolbox.agc(panel, None, **params)
    print 'starting plot'
    trace_centers = np.linspace(1,284, panel.size).reshape(-1,1)
    scalar = 284/(panel.size*0.1)
    panel['trace'][:,-1] = np.nan
    x = panel['trace'].copy()
    x[x< 0] = np.nan
    
    xx = ((x*scalar)+trace_centers).flatten().tolist()
    y = np.meshgrid(np.arange(1501), np.arange(284))[0].ravel().tolist(
    
    for i in range(1, len(xx), 1501):
        xx[i] = None
        y[i] = None
    
    #~ pylab.plot(x)
    #~ pylab.plot(np.zeros_like(x))
    #~ pylab.show()
    
    #~ inds = np.diff([x > 0])[0]
    
    #x[x < 0.0].fill(0.0)
    #x = [x > 0]
    #zero_crossings = np.where(x == 0)[0]+1
    #zero_crossings = zero_crossings[np.diff(zero_crossings) !=0 ]# 1]
    #zero_crossings = np.where(np.diff(np.signbit(x)))[0]+1
    #~ x = ((panel['trace']*scalar)+trace_centers).ravel()
    #~ xverts = np.split(x, inds)[::2]
    #~ yverts = np.split(y, inds)[::2]
    #~ polygons = [zip(xverts[i], yverts[i]) for i in range(0, len(xverts)) if len(xverts[i]) > 2]
    

    
    #print polygons.shape
    #print polygons
    x1 = ((panel['trace']*scalar)+trace_centers).ravel()
    y1 = np.meshgrid(np.arange(1501), np.arange(284))[0].ravel()
    xlines = np.split(x1, 284)
    ylines = np.split(y1, 284)
    lines = [zip(xlines[a],ylines[a]) for a in range(len(xlines))]  

    #~ lines = np.column_stack([x,y])
    #~ print lines
    #~ print lines.shape
    #~ print lines.ndim
    #~ print 'plotting'
    fig = pylab.figure()
    ax = fig.add_subplot(111)
    #~ col = collections.PolyCollection(polygons)
    #~ col.set_color('k')
    #~ ax.add_collection(col, autolim=True)
    col1 = collections.LineCollection(lines)
    col1.set_color('k')
    ax.add_collection(col1, autolim=True)
    ax.autoscale_view()
    pylab.fill(xx,y, 'k')
    pylab.xlim([0,284])
    pylab.ylim([0,1500])
    ax.set_ylim(ax.get_ylim()[::-1])
    pylab.tight_layout()
    pylab.show()