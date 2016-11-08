from nose import with_setup 
import numpy as np
import unittest


import PySeis
class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.file = './data/sample.su'
 
    def test_initialise_SU_file(self):
        data = PySeis.workspace()
        data.load(self.file, format="su")
        self.assertIsInstance(data.data,np.ndarray)
        data.save('./data/sample.npy')
        
        data1 = PySeis.workspace()
        data1.load('./data/sample.npy')
        #for name in data1.data.dtype.names:
            #if name != "data":
                #self.assertTrue((data.data[name] == data1.data[name]).all())
        #self.assertTrue((data.data.tolist() == data1.data.tolist()).all())
        
        
        
        
        
