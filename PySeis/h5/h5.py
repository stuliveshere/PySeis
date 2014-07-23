'''
initialises an existing h5 database for use with pyseis
'''
import tables as tb

class pyseis:
    def __init__(self, database):
        self.db = tb.openFile(database, mode = "r", title='test')