#!/usr/bin/python -d

#Copyright (c) 2013 Stewart Fletcher
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#the Software, and to permit persons to whom the Software is furnished to do so,
#subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


__description__ = '''
python SU stdin/stdout interface module

        data = readSU()
        writeSU(data)

uses custom dtypes for a very fast read/write to stdin/stdout
returns a single np.ndarray with dtype=sufile
a numpy 2d array of traces can be addressed as data['traces']
each header term can also be addressed via data['insertheaderterm']
'''

import numpy as np, sys, os, os.path
import tables as tb
su_header_dtype = np.dtype([
('tracl', np.int32),
('tracr', np.int32),
('fldr', np.int32),
('tracf', np.int32),
('ep', np.int32),
('cdp', np.int32),
('cdpt', np.int32),
('trid', np.int16),
('nvs', np.int16),
('nhs', np.int16),
('duse', np.int16),
('offset', np.int32),
('gelev', np.int32),
('selev', np.int32),
('sdepth', np.int32),
('gdel', np.int32),
('sdel', np.int32),
('swdep', np.int32),
('gwdep', np.int32),
('scalel', np.int16),
('scalco', np.int16),
('sx', np.int32),
('sy', np.int32),
('gx', np.int32),
('gy', np.int32),
('counit', np.int16),
('wevel', np.int16),
('swevel', np.int16),
('sut', np.int16),
('gut', np.int16),
('sstat', np.int16),
('gstat', np.int16),
('tstat', np.int16),
('laga', np.int16),
('lagb', np.int16),
('delrt', np.int16),
('muts', np.int16),
('mute', np.int16),
('ns', np.uint16),
('dt', np.uint16),
('gain', np.int16),
('igc', np.int16),
('igi', np.int16),
('corr', np.int16),
('sfs', np.int16),
('sfe', np.int16),
('slen', np.int16),
('styp', np.int16),
('stas', np.int16),
('stae', np.int16),
('tatyp', np.int16),
('afilf', np.int16),
('afils', np.int16),
('nofilf', np.int16),
('nofils', np.int16),
('lcf', np.int16),
('hcf', np.int16),
('lcs', np.int16),
('hcs', np.int16),
('year', np.int16),
('day', np.int16),
('hour', np.int16),
('minute', np.int16),
('sec', np.int16),
('timebas', np.int16),
('trwf', np.int16),
('grnors', np.int16),
('grnofr', np.int16),
('grnlof', np.int16),
('gaps', np.int16),
('otrav', np.int16), #179,180
('d1', np.float32), #181,184
('f1', np.float32), #185,188
('d2', np.float32), #189,192
('f2', np.float32), #193, 196
('ShotPoint', np.int32), #197,200
('unscale', np.int16), #201, 204
('TraceValueMeasurementUnit', np.int16),
('TransductionConstantMantissa', np.int32),
('TransductionConstantPower', np.int16),
('TransductionUnit', np.int16),
('TraceIdentifier', np.int16),
('ScalarTraceHeader', np.int16),
('SourceType', np.int16),
('SourceEnergyDirectionMantissa', np.int32),
('SourceEnergyDirectionExponent', np.int16),
('SourceMeasurementMantissa', np.int32),
('SourceMeasurementExponent', np.int16),
('SourceMeasurementUnit', np.int16),
('UnassignedInt1', np.int32),
('ns1', np.int32),
])







class Su(object):
    '''
    general class for reading, writing and creating SU files
    '''
    def __init__(self):
        pass

    def __call__(self):
        pass

class su:
    def __init__(self, database, **kwargs):
    #~ if not set(kwargs.keys()).issubset(keylist):
            #~ raise Exception("Invalid key in segy kwargs")
    #~ if not filename:
            #~ self.initialiseFramework()
    #~ else:
            #~ self.loadFramework()
        self.db = tb.openFile(database, mode = "w", title='test')

    def read(self, filelist):
        
        def read_ns(filename):
            return np.fromfile(filename, dtype=su_header_dtype, count=1)['ns']

        node = self.db.createGroup("/", 'jobname', 'PySeis Node')

        for index, file_ in enumerate(filelist):
            ns = read_ns(file_)
            sutype = np.dtype(su_header_dtype.descr + [('data', ('f4',ns))])
            th = self.db.createTable(node, "gather"+str(index), sutype, "Gather")
            #will need to add chunking at some point.
            with open(file_, 'rb') as f:
                data = np.fromfile(f, dtype=sutype)
                th.append(data)


if __name__ == '__main__':
    os.chdir('../../data/')
    path = '/misc/coalStor/University_QLD/crystal_mountain/2014/data/'
    filelist = [path+a for a in os.listdir(path) if '.su' in a]
    a = su('su_test.h5')
    a.read(filelist)


