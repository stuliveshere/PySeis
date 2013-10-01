import definitions as d
import numpy as np

file = open('./data/sample.sgy', 'rb')


txt =  file.read(1)


import binascii
print bin(int(binascii.hexlify(txt), 16))

