
#write a function which will flatten a cdp

import numpy as np
from toolbox import io

def _nmo_calc(tx, vels, offset):
        '''calculates the zero offset time'''
        t0 = np.sqrt(tx*tx - (offset*offset)/(vels*vels))
        return t0
        
@io
def nmo(dataset, **kwargs):
        offsets = np.unique(dataset['offset'])
        if 'smute' not in kwargs.keys(): kwargs['smute'] = 10000.
        ns = kwargs['ns']
        dt = kwargs['dt'] 
        tx = kwargs['times']
        
        for offset in offsets:

                aoffset = np.abs(offset.astype(np.float))
                #calculate time shift for each sample in trac
                t0 = _nmo_calc(tx, kwargs['vels'], aoffset)
                t0 = np.nan_to_num(t0)
                #calculate stretch between each sample
                stretch = 100.0*(np.pad(np.diff(t0),(0,1), 'reflect')-dt)/dt
                mute = kwargs['smute']
                filter = [(stretch >0.0) & ( stretch < mute)]
                inds = [dataset['offset'] == offset]
                subset = np.apply_along_axis(lambda m: np.interp(tx, t0, m), axis=-1, arr=dataset['trace'][inds])

                
                #~ subset[:,tx < np.amin(t0[filter])]  = 0.0
                #~ subset[:,tx > np.amax(t0[filter])] = 0.0
                dataset['trace'][inds] = subset * filter

        return dataset




@io
def co_nmo(dataset, **kwargs):
        offsets = np.unique(np.abs(dataset['offset']))
        cdps = np.sort(np.unique(dataset['cdp']))
        ns = kwargs['ns']
        dt = kwargs['dt'] 
        tx = kwargs['times']	
        if 'smute' not in kwargs.keys(): kwargs['smute'] = 10000.
        
        output = dataset.copy()
        output['trace'].fill(0.0)
        for offset in offsets:
                print offset
                aoffset = np.abs(offset.astype(np.float))
                #~ #calculate time shift for each sample in offset
                t0 = _nmo_calc(tx, kwargs['vels'], aoffset)
                t0 = np.nan_to_num(t0)
                stretch = 100.0*(np.pad(np.diff(t0),(0,1), 'reflect')-dt)/dt
                
                subset = dataset[np.abs(dataset['offset']) == aoffset]
                for trace in np.nditer(subset):
                        cdp = trace['cdp']
                        i = np.where(cdps == cdp)
                        tnew = t0[i,:].flatten()
                        s = np.zeros_like(stretch[i,:])
                        s[(stretch[i,:] >0.0) & ( stretch[i,:] < kwargs['smute'])] = 1
                
                        output['trace'][trace['tracr'],:] = np.interp(tx, tnew, trace['trace']) *s.flatten()
                        
        return output	