'''
Created on 20 Nov. 2018

@author: sfletcher
'''

import urllib2

if __name__ == '__main__':
    url = "http://www.velseis.com/publications/sample.sgy"
    response = urllib2.urlopen(url)
    _file = response.read()
    with open("sample.sgy", 'w') as f:
        f.write(_file)