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


if __name__ == "__main__":
	import numpy as np
	import segy_headers
	dtype=pack_dtype(values=segy_headers.segy_binary_header)
	print(dtype.fields)
	dtype1 = pack_dtype(dtype, [('test', ('B', 40), 400)])
	print(dtype1.fields)