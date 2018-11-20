#base class for reading external files. 
#to be extended for for different file types

class Read(object):
	def __init__(self, _file):
		pass
		
	def readFile(self):
		pass
		
class segyRead(Read):
	def __init__(self, _file):
		pass
		
	

if __name__== '__main__':
	test = segyRead("test")