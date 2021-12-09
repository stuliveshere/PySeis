'''
Allows us to download some open datasets for testing.
options currently include:

2D vibroseis line donated to public domain by Geofizyka Torun S.A, Poland
http://www.geofizyka.pl/2D_Land_vibro_data_2ms.tgz


https://wiki.seg.org/wiki/2D_Vibroseis_Line_001

there are other datasets availabe there as well. 

Created on 20 Nov. 2018
@author: sfletcher
'''

import urllib.request
import tarfile

url = "http://www.geofizyka.pl/2D_Land_vibro_data_2ms.tgz"
save_to = "2D_Land_vibro_data_2ms.tgz"


if __name__ == '__main__':
    #r = urllib.request.urlopen(url)
    #open(save_to , 'wb').write(r.read())
    tar = tarfile.open(save_to)
    tar.extractall()
    tar.close()