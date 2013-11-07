import numpy as np

def ibm2ieee(ibm): 
    """ Converts an IBM floating point number into IEEE format. """ 

    sign = ibm >> 31 & 0x01 

    exponent = ibm >> 24 & 0x7f 

    mantissa = ibm & 0x00ffffff 
    mantissa = (mantissa * np.float32(1.0)) / pow(2, 24) 

    ieee = (1 - 2 * sign) * mantissa * np.power(np.float32(16.0), exponent - 64) 

    return ieee 

def ieee2ibm(ieee): 
    ieee = ieee.astype(np.float32) 
    expmask = 0x7f800000 
    signmask = 0x80000000 
    mantmask = 0x7fffff 
    asint = ieee.view('i4') 
    signbit = asint & signmask 
    exponent = ((asint & expmask) >> 23) - 127 
    # The IBM 7-bit exponent is to the base 16 and the mantissa is presumed to 
    # be entirely to the right of the radix point. In contrast, the IEEE 
    # exponent is to the base 2 and there is an assumed 1-bit to the left of the 
    # radix point. 
    exp16 = ((exponent+1) // 4) 
    exp_remainder = (exponent+1) % 4 
    exp16 += exp_remainder != 0 
    downshift = np.where(exp_remainder, 4-exp_remainder, 0) 
    ibm_exponent = np.clip(exp16 + 64, 0, 127) 
    expbits = ibm_exponent << 24 
    # Add the implicit initial 1-bit to the 23-bit IEEE mantissa to get the 
    # 24-bit IBM mantissa. Downshift it by the remainder from the exponent's 
    # division by 4. It is allowed to have up to 3 leading 0s. 
    ibm_mantissa = ((asint & mantmask) | 0x800000) >> downshift 
    # Special-case 0.0 
    ibm_mantissa = np.where(ieee, ibm_mantissa, 0) 
    expbits = np.where(ieee, expbits, 0) 
    return signbit | expbits | ibm_mantissa
