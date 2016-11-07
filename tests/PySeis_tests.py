from nose import with_setup 

import PySeis

def setup():
    print "SETUP!"

def teardown():
    print "TEAR DOWN!"

@with_setup(setup, teardown)
def test_basic():
    print dir(PySeis)