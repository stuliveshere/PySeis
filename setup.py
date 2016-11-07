try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
config = {
  'name':'PySeis',
  'version':'0.1',
  'description':'Seismic Processing Package',
  'url':'http://github.com/stuliveshere/PySeis',
  'author':'Stewart Fletcher',
  'author_email':'mail@stuliveshere.com',
  'license':'MIT',
  'packages':['PySeis'],
  'zip_safe':False
  }

setup(**config)