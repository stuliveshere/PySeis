"""
Header mapping definitions between different seismic data formats.
Maps various formats (SEG-Y, SEG-D, SU, JavaSeis, RSF) to the internal seisdata schema.
"""

# SEG-Y to SeisData mappings
SEGY_TO_SEISDATA = {
    # Source related
    "source_line_number": "source_id",
    "source_point_number": "source_index",
    "source_coordinate_x": "source_x",
    "source_coordinate_y": "source_y",
    "source_depth": "source_z",
    "uphole_time_at_source": "uphole_time",
    
    # Receiver related
    "receiver_line_number": "receiver_id",
    "receiver_point_number": "receiver_index",
    "group_coordinate_x": "receiver_x",
    "group_coordinate_y": "receiver_y",
    "receiver_group_elevation": "receiver_z",
    
    # Trace related
    "trace_sequence_number": "trace_id",
    "trace_sequence_number_within_line": "trace_sequence_number",
    "source_to_receiver_distance": "offset",
    "total_static": "total_static",
    "trace_identification_code": "trace_identification_code",
    
    # Data related
    "number_of_samples": "num_samples",
    "sample_interval_in_microseconds": "sample_rate",
    "delay_recording_time": "recording_delay",
    
    # Coordinate system
    "coordinate_scalar": "coordinate_scalar",
    "elevation_scalar": "elevation_scalar"
}

# SEG-D to SeisData mappings
SEGD_TO_SEISDATA = {
    # Source related
    "source_id": "source_id",
    "source_point_index": "source_index",
    "source_x": "source_x",
    "source_y": "source_y",
    "source_depth": "source_z",
    "uphole_time": "uphole_time",
    
    # Receiver related
    "receiver_id": "receiver_id",
    "receiver_point_index": "receiver_index",
    "receiver_x": "receiver_x",
    "receiver_y": "receiver_y",
    "receiver_z": "receiver_z",
    
    # Trace related
    "trace_number": "trace_id",
    "trace_sequence_number": "trace_sequence_number",
    "offset": "offset",
    "total_static": "total_static",
    "trace_type": "trace_identification_code",
    
    # Data related
    "number_of_samples": "num_samples",
    "sample_interval": "sample_rate",
    "recording_delay": "recording_delay",
    
    # Coordinate system
    "coordinate_scale_factor": "coordinate_scalar",
    "elevation_scale_factor": "elevation_scalar"
}

# SU to SeisData mappings
SU_TO_SEISDATA = {
    # Source related
    "fldr": "source_id",
    "ep": "source_index",
    "sx": "source_x",
    "sy": "source_y",
    "sdepth": "source_z",
    "sut": "uphole_time",
    
    # Receiver related
    "tracr": "receiver_id",
    "tracf": "receiver_index",
    "gx": "receiver_x",
    "gy": "receiver_y",
    "gelev": "receiver_z",
    
    # Trace related
    "tracl": "trace_id",
    "tracr": "trace_sequence_number",
    "offset": "offset",
    "tstat": "total_static",
    "trid": "trace_identification_code",
    
    # Data related
    "ns": "num_samples",
    "dt": "sample_rate",
    "delrt": "recording_delay",
    
    # Coordinate system
    "scalco": "coordinate_scalar",
    "scalel": "elevation_scalar"
}

# JavaSeis to SeisData mappings
JS_TO_SEISDATA = {
    # Source related
    "sourceId": "source_id",
    "sourceIndex": "source_index",
    "sourceX": "source_x",
    "sourceY": "source_y",
    "sourceZ": "source_z",
    "upholeTime": "uphole_time",
    
    # Receiver related
    "receiverId": "receiver_id",
    "receiverIndex": "receiver_index",
    "receiverX": "receiver_x",
    "receiverY": "receiver_y",
    "receiverZ": "receiver_z",
    
    # Trace related
    "traceId": "trace_id",
    "traceSequenceNumber": "trace_sequence_number",
    "offset": "offset",
    "totalStatic": "total_static",
    "traceIdentificationCode": "trace_identification_code",
    
    # Data related
    "numberOfSamples": "num_samples",
    "sampleRate": "sample_rate",
    "recordingDelay": "recording_delay",
    
    # Coordinate system
    "coordinateScalar": "coordinate_scalar",
    "elevationScalar": "elevation_scalar"
}

# RSF to SeisData mappings
RSF_TO_SEISDATA = {
    # Source related
    "sid": "source_id",
    "sx": "source_index",
    "sx": "source_x",
    "sy": "source_y",
    "sz": "source_z",
    "ut": "uphole_time",
    
    # Receiver related
    "rid": "receiver_id",
    "rx": "receiver_index",
    "rx": "receiver_x",
    "ry": "receiver_y",
    "rz": "receiver_z",
    
    # Trace related
    "tid": "trace_id",
    "tsq": "trace_sequence_number",
    "off": "offset",
    "stat": "total_static",
    "ttyp": "trace_identification_code",
    
    # Data related
    "ns": "num_samples",
    "d1": "sample_rate",
    "o1": "recording_delay",
    
    # Coordinate system
    "scal": "coordinate_scalar",
    "elscal": "elevation_scalar"
}

def get_format_map(format_name: str) -> dict:
    """
    Get the mapping dictionary for converting from a specific format to SeisData.
    
    Parameters:
    - format_name (str): Name of the format ('segy', 'segd', 'su', 'js', 'rsf')
    
    Returns:
    - dict: Mapping dictionary for converting to SeisData format
    """
    format_maps = {
        'segy': SEGY_TO_SEISDATA,
        'segd': SEGD_TO_SEISDATA,
        'su': SU_TO_SEISDATA,
        'js': JS_TO_SEISDATA,
        'rsf': RSF_TO_SEISDATA
    }
    
    if format_name not in format_maps:
        raise ValueError(f"Unsupported format: {format_name}")
    
    return format_maps[format_name]

def get_reverse_map(format_name: str) -> dict:
    """
    Get the reverse mapping dictionary for converting from SeisData to a specific format.
    
    Parameters:
    - format_name (str): Name of the format ('segy', 'segd', 'su', 'js', 'rsf')
    
    Returns:
    - dict: Mapping dictionary for converting from SeisData format
    """
    forward_map = get_format_map(format_name)
    return {v: k for k, v in forward_map.items()}
