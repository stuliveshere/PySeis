import numpy as np

segd_general_header = np.dtype([
('fileno', 'S4'), #file number
('format', 'S4'), #format code  
('constants', 'S12'), #general constants
('year', 'S2'), #last 2 digits of year
('GH', 'S1'), #number of additional blocks
('julian', 'S3'), #julian day
('hour','S2'), #hour (UTC)
('min', 'S2'), #minute
('sec','S2'), #second
('mcode', 'S2'), #manufacturer's code
('mserial', 'S4'), #manufacturer's serial
('null', 'S6'), #not used
('bscan', 'S2'), #base scan interval
('polarity', 'S1'), #record polarity
('null2',  'S3'),
('type', 'S1'), #record type
('len', 'S3'), #record length
('STR', 'S2'),
('CS', 'S2'),
('SK', 'S2'),
('EC', 'S2'),
('EX', 'S2'),
])