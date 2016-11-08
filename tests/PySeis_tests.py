from nose import with_setup 
import unittest

import PySeis

#~ def setup():
    #~ print "SETUP!"

#~ def teardown():
    #~ print "TEAR DOWN!"

#~ @with_setup(setup, teardown)
#~ def test_basic():
    #~ print dir(PySeis)
 
class ContainerTests(unittest.TestCase):
 
    def test_container_build(self):
        print dir(PySeis)
        data = PySeis.workspace()

