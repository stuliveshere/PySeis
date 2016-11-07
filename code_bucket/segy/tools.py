#functions for reading and writing segy files

import tables as tb
import os, sys

class segy:
    def __init__(self):
        pass
        
    def read(self, filelist):
        pass
        
        
    def read_EBCDIC(self):
        ''''function to read EBCDIC header'''
        with open(file_, 'rb') as f:
            header = np.fromfile(f, dtype='u2', count=3200/2)
            if np.any(np.diff(header)):
                f.seek(0)
                return f.read(3200).decode('EBCDIC-CP-BE').encode('ascii')
            else:
                return None

        #~ def read_bheader(file_):
            #~ ''''function to read binary header'''
            #~ with open(file_, 'rb') as f:
                #~ f.seek(3200)
                #~ binary = np.fromstring(f.read(400), dtype=segy_binary_header_dtype)
                #~ #endian sanity checks. this is pretty crude and will need revisting.
                #~ try:
                    #~ assert 0 < binary['format'] < 9
                #~ except AssertionError:
                    #~ binary = binary.byteswap()
                #~ return binary

        #~ def num_traces(file_, ns):
                #~ with open(file_, 'rb') as f:
                    #~ f.seek(0, os.SEEK_END)
                    #~ size = f.tell()
                    #~ nt = (size-3600.0)/(240.0+ns*4.0)
                    #~ assert nt % 1 == 0
                #~ return nt

        #~ def ibm2ieee(ibm):
            #~ s = ibm >> 31 & 0x01 
            #~ exp = ibm >> 24 & 0x7f 
            #~ fraction = (ibm & 0x00ffffff).astype(np.float32) / 16777216.0
            #~ ieee = (1.0 - 2.0 * s) * fraction * np.power(np.float32(16.0), exp - 64.0) 
            #~ return ieee
        
        
        #~ node = self.db.createGroup("/", 'jobname', 'PySeis Node')
        #~ fh = self.db.createTable(node, 'FH', segy_textual_header_dtype, "EBCDIC File Header")
        #~ bh = self.db.createTable(node, 'BH', segy_binary_header_dtype, "Binary File Header")
        #~ th = self.db.createTable(node, "TH", segy_trace_header_dtype, "Headers")
        #~ td = self.db.createTable(node, "TD", np.dtype([('data', ('f4',ns))]), "Headers")

        #~ for file_ in filelist:
            #~ EBCDIC = read_EBCDIC(file_)
            #~ if EBCDIC: fh.append(EBCDIC)
            #~ bheader = read_bheader(file_)
            #~ bh.append(bheader)
            #~ self.db.flush()

            #~ assert np.any(np.diff(bh.cols.hns[:])) == False #check ns is constant
            #~ assert np.any(np.diff(bh.cols.hdt[:])) == False #check ns is constant
            #~ ns = bh.cols.hns[0]
            #~ dt = bh.cols.hdt[0]

        #~ for index, file_ in enumerate(filelist):

            #will need to add chunking at some point.
            #~ counts = 0
            #~ with open(file_, 'rb') as f:
                #~ f.seek(3600+240)
                #~ try:
                    #~ while True:
                        #~ data = np.fromfile(f, dtype=ibmtype, count=int(1))
                        #~ data['data'] = ibm2ieee(data['data'])
                        #~ th.append(data.astype(ieeetype))
                        #~ th.flush()
                #~ except:
                    #~ data = np.fromfile(f, dtype=ibmtype)
                    #~ data['data'] = ibm2ieee(data['data'])
                    #~ th.append(data.astype(ieeetype))
                    #~ th.flush()
                        

            


if __name__ == '__main__':
    os.chdir('../../data/')
    path = '/coalStor/University_QLD/crystal_mountain/2014/data/segy/'
    filelist = [path+a for a in os.listdir(path) if '.sgy' in a]
    a = database('segy_test.h5')
    a.read(filelist)