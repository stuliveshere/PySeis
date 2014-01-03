import pylab

x = [1e4, 1e5, 1e6, 1e7]

hashed = [0.110387086868,
	0.755256175995,
	4.53062009811,
	68.7740361691]
	
brute = [19.4763548374,
	179.688730955,
	2088.64743304, 
	69576.9061649]
	
pylab.loglog(x, hashed, '-o', label='hash')
pylab.loglog(x, brute, '-o', label='brute')
pylab.legend()
pylab.show()