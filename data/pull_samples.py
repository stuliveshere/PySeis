'''
Created on 20 Nov. 2018

@author: sfletcher
'''

import urllib2

if __name__ == '__main__':
    urls = ["http://www.velseis.com/publications/sample.sgy", "http://www.velseis.com/publications/sample.su"]
    for url in urls:
        fname = url.split("/")[-1]
        response = urllib2.urlopen(url)
        data = response.read()
        with open(fname, 'w') as f:
            f.write(data)