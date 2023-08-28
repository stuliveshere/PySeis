import sys
sys.path.insert(1, '../../PySeis')
import numpy as np
from PySeis.io.segy import Segy
from os.path import join

# Define base path
base_path = "../data/"

#define the input file
input_sgy = join(base_path, "Line_001.sgy")

#import dataset
''' 
when you initialise the class (e.g. Segy("somefile.sgy)) it will 
		readEBCDIC()
		readBheader()
		readNS()
		report() (if verbose=1)

the EBCDIC is stored in self.params["EBCDIC"]
the BHEADER is stores as an array self.bheader as well as dictionary values in self.params["BHEADER"]

'''
input = Segy(input_sgy, verbose=1)
input.read() 
