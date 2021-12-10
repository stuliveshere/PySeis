from tools import pack_dtype
from headers import segy_binary_header, segy_trace_header
import numpy as np
class fopen(object):
    '''
    Opens a file for reading, writing or parsing.

    Parameters
    ----------

    filename : str
        Path of file to open

    mode : {'r', 'r+'}
        File access mode. Read-only ('r', default) or read-write('r+').

    encoding: {'segy', 'su', 'npy'}
        the data encoding

    chunks : {-1, 1, int}, 
        File chunk mode.  number of "traces", where trace can be 
        considered a 1D array sliced along the fast axis (time)
        1 - n traces.  -1 (default) will attempt to automatically
        calculate the optimal chunk size.

        if sort is used, the chunk size will be set to the size
        of the primary sort.

    mmap : bool
        whether to try and memmap the file. Defaults to false

    sort : {None, (str, None)}
        sort the IO based upon a dtype header. 2nd order sort also available


    '''
    def __init__(self, file, mode='r', encoding='npy', chunks=-1, mmap=False, sort=None):
        self.file = file 
        self.mode = mode 
        self.encoding = encoding
        self.chunks = chunks 
        self.mmap = mmap
        self.sort = sort
        self.fh = None #file handle
        self.params = {
            "dtype": None,
            "EBCDIC": "",
            "BHEADER": None,
            "NS": None,
        }
        
        if mode == "r": self.read()  

    def __iter__(self):
        return self

    def __next__(self):
        if self.encoding == 'sgy':
            chunk = np.fromfile(self.fh, dtype=self._dtype, count=self.chunks)
            if chunk.size !=0:
                return chunk
            else:
                raise StopIteration

    def read(self):
        if self.encoding == 'npy':
            self.fh = np.load(self.file, mmap_mode='r')

        elif self.encoding == "sgy":
            with open(file=self.file, mode="rt", encoding="cp500") as f:
                f.seek(0)
                self.params["EBCDIC"] = "\n".join([f.read(80) for i in range(40)])
                f.close()
            with open(self.file, 'rb') as f:
                f.seek(3200)
                _dtype=pack_dtype(values=segy_binary_header)
                _dtype = _dtype.newbyteorder()
                self.params['BHEADER'] = np.fromfile(f, dtype=_dtype, count=1)[0]
                self.params['NS'] = self.params['BHEADER']['hns']
                self._dtype=pack_dtype(values=segy_trace_header + [('trace', ('<f4', self.params['NS']), 240)])
                self._dtype = self._dtype.newbyteorder()
                self.fh = open(self.file, 'rb')
                self.fh.seek(3600)

        elif self.encoding == "su":
            _dtype=pack_dtype(su_trace_header)
            self.params['NS'] = ns1 = np.fromstring(self.file, dtype=_dtype, count=1)['ns'][0]
            self._dtype=pack_dtype(values=su_trace_header + [('trace', ('<f4', self.params['NS']), 240)])
            self.fh = open(self.file, 'rb')
        else: 
            raise Exception("not a valid encoding")
            
  
        

    def write(self):
        pass

    def parse(self):
        pass


if __name__ == "__main__":
    f = fopen("../../data/Line_001.sgy", encoding='sgy', chunks=100)
    for trace in f:
        print(trace['fldr'])




    




