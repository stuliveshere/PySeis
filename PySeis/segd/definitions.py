import numpy as np

segd_general_header = np.dtype([
('fileno', 'S4'), #file number
('format', 'S4'), #format code  
('constants', 'S12'), #general constants
('year', 'S2'), #last 2 digits of year
('GH', 'uint8'), #number of additional blocks
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
('len1', 'uint16'), #record length
('len2', 'uint16'), #record length
('len3', 'uint16'), #record length
('STR', 'S2'),
('CS', 'S2'),
('SK', 'S2'),
('EC', 'S2'),
('EX', 'S2'),
])

segd_general_header_list =[
('fileno', 4), #file number
('format', 4), #format code  
('constants', 12), #general constants
('year', 2), #last 2 digits of year
('GH', 1), #number of additional blocks
('julian',3), #julian day
('hour',2), #hour (UTC)
('min', 2), #minute
('sec',2), #second
('mcode', 2), #manufacturer's code
('mserial', 4), #manufacturer's serial
('null', 6), #not used
('bscan', 2), #base scan interval
('polarity', 1), #record polarity
('null2',  3),
('type', 1), #record type
('len', 3), #record length
('STR', 2),
('CS', 2),
('SK', 2),
('EC', 2),
('EX', 2),
]