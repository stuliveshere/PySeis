from nose import with_setup 
import numpy as np
import unittest


import PySeis
from PySeis import Stream
class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.infile = './data/sample.su'
        self.outfile = './data/sample.npy'
 
    def test_initialise_SU_file(self):
        PySeis.loadSU(self.infile, self.outfile)
        data = Stream(self.outfile, "test.npy")
        for gather in data:
            print np.unique(gather['fldr'])

        
        

        
        
        
        
        
