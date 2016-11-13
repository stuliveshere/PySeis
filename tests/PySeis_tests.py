from nose import with_setup 
import numpy as np
import unittest


import PySeis
class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.infile = './data/sample.su'
        self.outfile = './data/sample.npy'
 
    def test_initialise_SU_file(self):
        PySeis.su.loadSU(self.infile, self.outfile)
        data = PySeis.su.Stream(self.outfile, "test.npy")
        print data.indata.shape
        data.chunk(lambda x: x/2.0, args=[])
        
        

        
        
        
        
        
