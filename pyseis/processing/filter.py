import numpy as np
from scipy.signal import butter, lfilter, convolve2d

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y	

@io
def bandpass(dataset, **kwargs):
        
        # Sample rate and desired cutoff frequencies (in Hz).
        fs = 1./kwargs['dt']
        lowcut = kwargs['lowcut']
        highcut = kwargs['highcut']
            
        dataset['trace'] = butter_bandpass_filter(dataset['trace'], lowcut, highcut, fs, order=6)
        return dataset

