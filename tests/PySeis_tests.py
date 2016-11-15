from nose import with_setup 
import numpy as np
import unittest


import PySeis
from PySeis import Stream
class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.path = "/home/sfletcher/Alaska/"

 
    def test_initialise_SU_file(self):
        PySeis.loadSU(self.path+"raw.su", self.path+"raw.npy")
        data = Stream(self.path+"raw.npy", self.path+"agc.npy")
        params = {}
        for gather in data:
            PySeis.processing.toolbox.agc(gather, **params)
        data.close()
        PySeis.saveSU(self.path+"agc.npy", self.path+"agc.su")

        
        

        
        
        
        
        
