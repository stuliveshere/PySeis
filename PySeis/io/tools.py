import numpy as np

def pack_dtype(_dtype=None, values=[]): #name, format, offset
	names = []
	formats = []
	offsets = []
	if _dtype:
		names = list(_dtype.fields.keys())
		for key in names:
			formats.append(_dtype.fields[key][0])
			offsets.append((_dtype.fields[key][1]))
	if values:
		for entry in values:
			names.append(entry[0])
			formats.append(entry[1])
			offsets.append(entry[2])
	return np.dtype({
	'names': names,
	'formats': formats,
	'offsets': offsets,
	})

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
