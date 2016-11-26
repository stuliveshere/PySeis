from nose import with_setup 
import numpy as np
import unittest


import PySeis
from PySeis import Stream
class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.path = "/home/stewart/data/su/"

 
    def test_initialise_SU_file(self):
        PySeis.loadSU(self.path+"test.su", self.path+"raw.npy")
        data = Stream(self.path+"raw.npy", self.path+"agc.npy")
        params = {}
        print "beginning iteration"
        for gather in data:
            PySeis.processing.toolbox.agc(gather, **params)
            gather.save()
            gather.close()
        #data.close()
        PySeis.saveSU(self.path+"agc.npy", self.path+"agc.su")

        
        

        
        
        
        
        
