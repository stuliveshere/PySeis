import PySeis.su as su
import numpy as np

data = su.readSU('sample.su')

cleaned_data = np.zeros_like(data)

keys = ['trace', 'tracl', 'fldr', 'tracf', 'cdp', 'nhs', 'sx', 'sy', 'gx', 'gy', 'ns', 'dt']

for key in keys:
	cleaned_data[key] = data[key]
	
su.writeSU(cleaned_data, 'cleaned_sample.su')


