'''
Created on 20 Nov. 2018

@author: sfletcher
'''

import requests

urlpath = "https://certmapper.cr.usgs.gov/data/NPRA/seismic/1975/30x_75/DMUX/"
urlfiles = ["L23699.SGY"]+["L2370%d.SGY" %a for a in range(10)]
urls = [urlpath+a for a in urlfiles]
print(urls)


if __name__ == '__main__':
    for url in urls:
        fname = "./data/"+url.split("/")[-1]
        r = requests.get(url)
        open(fname , 'wb').write(r.content)