#~ Weiner filtering is a 2 liner -> 

#~ H = fft(kernel)
#~ deconvolved = ifftshift(ifft(fft(signal)*np.conj(H)/(H*np.conj(H) + lambda**2)))

#~ where lambda is your regularisation parameter, and white noise is assumed. There 
#~ are various methods for choosing lambda optimally, but most people tend to use 
#~ trial and error.

#from http://mail.scipy.org/pipermail/scipy-user/2011-August/030148.html