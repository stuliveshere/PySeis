import tables as tb
import numpy as np

class segy_file_header(tb.IsDescription):
    TFH1 = tb.StringCol(80)
    TFH2 = tb.StringCol(80)
    TFH3 = tb.StringCol(80)
    TFH4 = tb.StringCol(80)
    TFH5 = tb.StringCol(80)
    TFH6 = tb.StringCol(80)
    TFH7 = tb.StringCol(80)
    TFH8 = tb.StringCol(80)
    TFH9 = tb.StringCol(80)
    TFH10 = tb.StringCol(80)
    TFH11 = tb.StringCol(80)
    TFH12 = tb.StringCol(80)
    TFH13 = tb.StringCol(80)
    TFH14 = tb.StringCol(80)
    TFH15 = tb.StringCol(80)
    TFH16 = tb.StringCol(80)
    TFH17 = tb.StringCol(80)
    TFH18 = tb.StringCol(80)
    TFH19 = tb.StringCol(80)
    TFH20 = tb.StringCol(80)
    TFH21 = tb.StringCol(80)
    TFH22 = tb.StringCol(80)
    TFH23 = tb.StringCol(80)
    TFH24 = tb.StringCol(80)
    TFH25 = tb.StringCol(80)
    TFH26 = tb.StringCol(80)
    TFH27 = tb.StringCol(80)
    TFH28 = tb.StringCol(80)
    TFH29 = tb.StringCol(80)
    TFH30 = tb.StringCol(80)
    TFH31 = tb.StringCol(80)
    TFH32 = tb.StringCol(80)
    TFH33 = tb.StringCol(80)
    TFH34 = tb.StringCol(80)
    TFH35 = tb.StringCol(80)
    TFH36 = tb.StringCol(80)
    TFH37 = tb.StringCol(80)
    TFH38 = tb.StringCol(80)
    TFH39 = tb.StringCol(80)
    TFH40 = tb.StringCol(80)
    


segy_binary_header_dtype = np.dtype([
    ('jobid', '>i4'),
    ('lino', '>i4'),
    ('reno', '>i4'),
    ('ntrpr', '>i2'),
    ('nart', '>i2'),
    ('hdt', '>u2'),
    ('dto', '>u2'),
    ('hns', '>u2'),
    ('nso', '>u2'),
    ('format', '>i2'),
    ('fold', '>i2'),
    ('tsort', '>i2'),
    ('vscode', '>i2'),
    ('hsfs', '>i2'),
    ('hsfe', '>i2'),
    ('hslen', '>i2'),
    ('hstyp', '>i2'),
    ('schn', '>i2'),
    ('hstas', '>i2'),
    ('hstae', '>i2'),
    ('htatyp', '>i2'),
    ('hcorr', '>i2'),
    ('bgrcv', '>i2'),
    ('rcvm', '>i2'),
    ('mfeet', '>i2'),
    ('polyv', '>i2'),
    ('vpol', '>i2'),
    ('unassigned_1', (np.str_,   240)),
    ('segyrev', '>i2'),
    ('fixedlen', '>i2'),
    ('numhdr', '>i2'),
    ('unassigned_2', (np.str_,   94)),
])


segy_textual_header_dtype = np.dtype([
    ('TFH1', (np.str_,   80)),
    ('TFH2', (np.str_,   80)),
    ('TFH3', (np.str_,   80)),
    ('TFH4', (np.str_,   80)),
    ('TFH5', (np.str_,   80)),
    ('TFH6', (np.str_,   80)),
    ('TFH7', (np.str_,   80)),
    ('TFH8', (np.str_,   80)),
    ('TFH9', (np.str_,   80)),
    ('TFH10', (np.str_,   80)),
    ('TFH11', (np.str_,   80)),
    ('TFH12', (np.str_,   80)),
    ('TFH13', (np.str_,   80)),
    ('TFH14', (np.str_,   80)),
    ('TFH15', (np.str_,   80)),
    ('TFH16', (np.str_,   80)),
    ('TFH17', (np.str_,   80)),
    ('TFH18', (np.str_,   80)),
    ('TFH19', (np.str_,   80)),
    ('TFH20', (np.str_,   80)),
    ('TFH21', (np.str_,   80)),
    ('TFH22', (np.str_,   80)),
    ('TFH23', (np.str_,   80)),
    ('TFH24', (np.str_,   80)),
    ('TFH25', (np.str_,   80)),
    ('TFH26', (np.str_,   80)),
    ('TFH27', (np.str_,   80)),
    ('TFH28', (np.str_,   80)),
    ('TFH29', (np.str_,   80)),
    ('TFH30', (np.str_,   80)),
    ('TFH31', (np.str_,   80)),
    ('TFH32', (np.str_,   80)),
    ('TFH33', (np.str_,   80)),
    ('TFH34', (np.str_,   80)),
    ('TFH35', (np.str_,   80)),
    ('TFH36', (np.str_,   80)),
    ('TFH37', (np.str_,   80)),
    ('TFH38', (np.str_,   80)),
    ('TFH39', (np.str_,   80)),
    ('TFH40', (np.str_,   80)),
])

segy_trace_header_dtype = np.dtype([
    ('tracl',  '>i4'),
    ('tracr',  '>i4'),
    ('fldr',   '>i4'),
    ('tracf',  '>i4'),
    ('ep',     '>i4'),
    ('cdp',    '>i4'),
    ('cdpt',   '>i4'),
    ('trid',   '>i2'),
    ('nvs',    '>i2'),
    ('nhs',    '>i2'),
    ('duse',   '>i2'),
    ('offset', '>i4'),
    ('gelev',  '>i4'),
    ('selev',  '>i4'),
    ('sdepth', '>i4'),
    ('gdel',   '>i4'),
    ('sdel',   '>i4'),
    ('swdep',  '>i4'),
    ('gwdep',  '>i4'),
    ('scalel', '>i2'),
    ('scalco', '>i2'),
    ('sx',     '>i4'),
    ('sy',     '>i4'),
    ('gx',     '>i4'),
    ('gy',     '>i4'),
    ('counit', '>i2'),
    ('wevel',   '>i2'),
    ('swevel',  '>i2'),
    ('sut',     '>i2'),
    ('gut',     '>i2'),
    ('sstat',   '>i2'),
    ('gstat',   '>i2'),
    ('tstat',   '>i2'),
    ('laga',    '>i2'),
    ('lagb',    '>i2'),
    ('delrt',   '>i2'),
    ('muts',    '>i2'),
    ('mute',    '>i2'),
    ('ns',      '>i2'),
    ('dt',      '>i2'),
    ('gain',    '>i2'),
    ('igc',    '>i2'),
    ('igi',    '>i2'),
    ('corr',   '>i2'),
    ('sfs',    '>i2'),
    ('sfe',    '>i2'),
    ('slen',   '>i2'),
    ('styp',   '>i2'),
    ('stas',   '>i2'),
    ('stae',   '>i2'),
    ('tatyp',  '>i2'),
    ('afilf',  '>i2'),
    ('afils',  '>i2'),
    ('nofilf', '>i2'),
    ('nofils', '>i2'),
    ('lcf',    '>i2'),
    ('hcf',    '>i2'),
    ('lcs',    '>i2'),
    ('hcs',    '>i2'),
    ('year',   '>i2'),
    ('day',    '>i2'),
    ('hour',   '>i2'),
    ('minute', '>i2'),
    ('sec',    '>i2'),
    ('timbas', '>i2'),
    ('trwf',   '>i2'),
    ('grnors', '>i2'),
    ('grnofr', '>i2'),
    ('grnlof', '>i2'),
    ('gaps',   '>i2'),
    ('otrav',  '>i2'),
    ('cdpx',   '>i4'),
    ('cdpy',   '>i4'),
    ('iline',  '>i4'),
    ('xline',  '>i4'),
    ('shnum',  '>i4'),
    ('shsca',  '>i2'),
    ('tval',   '>i2'),
    ('tconst4', '>i4'),
    ('tconst2', '>i2'),
    ('tunits', '>i2'),
    ('device', '>i2'),
    ('tscalar', '>i2'),
    ('stype',  '>i2'),
    ('sendir', '>i4'),
    ('unknown', '>i2'),
    ('smeas4', '>i4'),
    ('smeas2', '>i2'),
    ('smeasu', '>i2'),
    ('unass1', '>i4'),
    ('unass2', '>i4')
])

