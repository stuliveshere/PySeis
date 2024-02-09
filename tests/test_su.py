import numpy as np
import unittest
import PySeis.io.su as su  # Import the su module

class ContainerTests(unittest.TestCase):
    
    def setUp(self):
        self.path = "/home/stewart/data/su/"
        self.su = su.SU()  # Create an instance of SU

    def test_initialise_SU_file(self):
        # Your test code here, using self.su
        # Example: self.su.initialize()
        pass

# More test methods as needed
