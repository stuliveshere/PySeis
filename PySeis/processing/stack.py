import numpy as np

def _stack_gather(gather):
        '''stacks a single gather into a trace.
        uses header of first trace. normalises
        by the number of traces'''
        gather['trace'][0] = np.sum(gather['trace'], axis=-2)/np.sqrt(gather.size)
        return gather[0]

@io	
def stack(dataset, **kwargs):
        cdps = np.unique(dataset['cdp'])
        sutype = np.result_type(dataset)
        result = np.zeros(cdps.size, dtype=sutype)
        for index, cdp in enumerate(cdps):
                gather = dataset[dataset['cdp'] == cdp]
                trace = _stack_gather(gather)
                result[index] = trace
        return result