import definitions as d
import numpy as np

file = open('./data/sample.sgy', 'rb')


for i in range(40):
	print  file.read(80).decode('EBCDIC-CP-BE') 
	
print np.array(file.read(400), dtype=d.segy_binary_header)
