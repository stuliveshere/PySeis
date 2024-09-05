import numpy as np

def pack_dtype(_dtype=None, values=[], order=">"): 
    """
    This function constructs a new numpy dtype object based on an existing dtype 
    and a list of additional field specifications. The dtype can also be set 
    to use a specific byte order.

    Parameters:
    _dtype (np.dtype, optional): Existing numpy dtype object.
    values (list of tuple, optional): List of field specifications.
    order (str, optional): Byte order for the data.

    Returns:
    np.dtype: New numpy dtype object.
    """
    
    # Initialize lists to store names, formats and offsets
    names = []
    formats = []
    offsets = []
    
    # If an existing dtype object is provided, extract its field specifications
    if _dtype:
        names = list(_dtype.fields.keys())
        for key in names:
            formats.append(_dtype.fields[key][0])
            offsets.append((_dtype.fields[key][1]))
    
    # If additional field specifications are provided, append them to the lists
    if values:
        for entry in values:
            names.append(entry[0])
            formats.append(entry[1])
            offsets.append(entry[2])
    
    # Construct a new dtype object using the specifications
    new_dtype = np.dtype({
        'names': names,
        'formats': formats,
        'offsets': offsets,
    })
    
    # Return the new dtype object with the specified byte order
    return new_dtype.newbyteorder(order)



def memory():
	"""
	Get node total memory and memory usage
	"""
	with open('/proc/meminfo', 'r') as mem:
		ret = {}
		tmp = 0
		for i in mem:
			sline = i.split()
			if str(sline[0]) == 'MemTotal:':
				ret['total'] = int(sline[1])
			elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
				tmp += int(sline[1])
		ret['free'] = tmp
		ret['used'] = int(ret['total']) - int(ret['free'])
		return ret
