import definitions as d
import numpy as np

file = open('./data/sample.sgy', 'rb')


for i in range(40):
	file.read(80).decode('EBCDIC-CP-BE') 
	
	
bh = file.read(400)

bh = np.array(bh, dtype=d.segy_binary_file_header)

print bh['jobid']

