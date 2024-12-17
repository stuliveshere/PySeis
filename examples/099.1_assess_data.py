import sys
sys.path.insert(1, '../../PySeis')
import numpy as np
from os.path import join
from PySeis.io.su import SU

# Define base path
base_path = "../data/"

#define the input file
input_su = join(base_path, "Line_001.sgy.su")


'''
reading an SU file into numpy requires checking the number of samples, building the correct dtype, then importing.
It can be done as a function, but I've left this in a class structure similiar to the Segy class. 
This allows a bit more flexibility as it separates the setup from the read
'''
handle = SU(input_su)
