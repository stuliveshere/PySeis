


from toolbox import typeSU
import numpy as np
from matplotlib import collections
from timeit import Timer

def func(panel): 
    
    panel['trace'][:,-1] = np.nan
    trace_centers = np.linspace(1,284, panel.size).reshape(-1,1)
    scalar = 284/(panel.size*0.5)
    y = np.meshgrid(np.arange(1501), np.arange(284))[0].ravel() 
    offsets = (np.meshgrid(np.arange(1501), np.arange(284))[1]+1).ravel()
    x = ((panel['trace']*scalar)+trace_centers).ravel()
    fig,ax = pylab.subplots()
    ax.fill_betweenx(y,offsets,x,where=(x>offsets),color='k')
    pylab.xlim([0,284])
    pylab.ylim([0,1500])
    ax.set_ylim(ax.get_ylim()[::-1])
    pylab.tight_layout()
    pylab.show(block=False)

dmap = np.memmap(file, dtype=toolbox.typeSU(1501), mode='r')
eps = np.unique(dmap['ep'])
for ep in eps[:1]:
    panel = dmap[dmap['ep'] == ep].copy()
    panel = toolbox.agc(panel, None, **params)
    t = Timer("""func(panel)""", setup="from __main__ import func; from __main__ import panel")
    print t.timeit(100)


#777.01802206