from nose import with_setup 
import numpy
import unittest

import PySeis

class ContainerTests(unittest.TestCase):
    def setUp(self):
        self.suFile = './data/sample.su'
 
    def test_initialise_SU_file(self):
        data = PySeis.workspace()
        data.initialise(self.suFile)
        self.assertIsInstance(data.data,numpy.ndarray)
        
        
        
