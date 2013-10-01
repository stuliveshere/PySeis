import definitions as d
import numpy as np

file = open('./data/sample.sgy', 'rb')


for i in range(40):
	print  file.read(80).decode('EBCDIC-CP-BE') 
