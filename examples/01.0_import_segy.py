import sys
sys.path.insert(1, '../../PySeis')
import numpy as np
from PySeis.io.segy import Segy
from os.path import join

# Define base path
base_path = "/misc/softwareStor/sfletcher/git/segIO"

#define the input file
input_sgy = join(base_path, "temp.sgy")

#import dataset
''' 
when you initialise the class (e.g. Segy("somefile.sgy)) it will 
		readEBCDIC()
		readBheader()
		readNS()
		report() (if verbose=1)
        
and create self._dtype.

the EBCDIC is stored in self.params["EBCDIC"]
the BHEADER is stores as an array self.bheader as well as dictionary values in self.params["BHEADER"]

However this step DOES NOT read in the data.

'''
input = Segy(input_sgy)
input.read()
input.write(input_sgy+".su", input_sgy+"_test.sgy")

#read dataset
'''
the following step reads in the segy and converts to a .su file.

I have been tossing up between between .npy and .su, with the only difference being a .npy header 

however a) np.memmap reads/writes binary blobs (e.g. .su) and .su means we can use Seismic Unix modules.

the output location is the same as the input location, with .su added to the filename.

'''
# input.read() #generates a 425MB file on disk.
#read the numpy data
# data = np.memmap(input_sgy+".su", dtype=input._dtype, mode='r+')
# can also use np.fromfile(...)
# print("npy data: ", data[0])

#read the same data generated by SU's segyread
#big endian!
# data = np.memmap("../data/Line_001_2.su", dtype=input._dtype)
# print("su data: ", data[0])

