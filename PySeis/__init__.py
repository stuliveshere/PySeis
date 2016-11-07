#test for requirements
import sys

try:
        from numpy import pad
except ImportError:
        print "something wrong with numpy"
        sys.exit()
        
try:
        from scipy.signal import fftconvolve
except ImportError:
        print "something wrong with scipy"
        sys.exit()


#cleanup namespace
del pad
del fftconvolve
del sys
        
from . import core
from .core import *