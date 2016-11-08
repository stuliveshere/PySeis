'''
process a dataset in chunks.

eventually this will require 1, 2 or 3 dimensional keys,
which means we need to track the sort order of the data
(or have worker request sort order for chunking)

ideally we also want the calculation to be able to do multiple things.
effectively the user should write calculation, and the chunking 
should be handled extenally. a chunking decorator perhaps?
'''


import numpy as np
import multiprocessing

def main():
    data = np.memmap('data.dat', dtype=np.float, mode='r')
    pool = multiprocessing.Pool()
    results = pool.imap(calculation, chunks(data))
    results = np.fromiter(results, dtype=np.float)

def chunks(data, chunksize=100):
    """Overly-simple chunker..."""
    intervals = range(0, data.size, chunksize) + [None]
    for start, stop in zip(intervals[:-1], intervals[1:]):
        yield np.array(data[start:stop])

def calculation(chunk):
    """Dummy calculation."""
    return chunk.mean() - chunk.std()

if __name__ == '__main__':
    main()