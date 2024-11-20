import sys
import os
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from construct import *
from pyseis.io.tools import ibm2ieee, ieee2ibm  # Now use absolute import

class IBMFloatAdapter(Adapter):
    def _decode(self, obj, context, path):
        return ibm2ieee(obj)
    
    def _encode(self, obj, context, path):
        return ieee2ibm(obj)

# Add EBCDIC to ASCII conversion adapter
class EBCDICAdapter(Adapter):
    def _decode(self, obj, context, path):
        # Convert EBCDIC to ASCII
        try:
            return obj.decode('cp037')  # cp037 is the EBCDIC code page
        except:
            return obj
    
    def _encode(self, obj, context, path):
        # Convert ASCII to EBCDIC if needed
        try:
            return obj.encode('cp037')
        except:
            return obj

# SEGY format definition
segy_format = Struct(
    "ebcdic" / Bytes(3200),

    "binary" / Struct(
        "job_id" / Int32ub,
        "line_number" / Int32ub,
        "reel_number" / Int32ub,
        "number_of_data_traces_per_ensemble" / Int16ub,
        "number_of_auxiliary_traces_per_ensemble" / Int16ub,
        "sample_interval" / Int16ub,
        "sample_interval_original" / Int16ub,
        "number_of_samples_per_trace" / Int16ub,
        "number_of_samples_original" / Int16ub,
        "data_sample_format_code" / Int16ub,
        "ensemble_fold" / Int16ub,
        "trace_sorting_code" / Int16ub,
        "vertical_sum_code" / Int16ub,
        "sweep_frequency_start" / Int16ub,
        "sweep_frequency_end" / Int16ub,
        "sweep_length" / Int16ub,
        "sweep_type_code" / Int16ub,
        "trace_number_of_sweep_channel" / Int16ub,
        "sweep_trace_taper_length_start" / Int16ub,
        "sweep_trace_taper_length_end" / Int16ub,
        "taper_type" / Int16ub,
        "correlated_traces" / Int16ub,
        "binary_gain_recovered" / Int16ub,
        "amplitude_recovery_method" / Int16ub,
        "measurement_system" / Int16ub,
        "impulse_signal_polarity" / Int16ub,
        "vibratory_polarity_code" / Int16ub,
        None / Bytes(340)  # Remaining bytes for custom data
    ),

    "traces" / Array(
        lambda this: (
            this.binary.number_of_data_traces_per_ensemble +
            this.binary.number_of_auxiliary_traces_per_ensemble
        ),
        Struct(
            "header" / Struct(
                "trace_sequence_number_within_line" / Int32ub,
                "trace_sequence_number_within_file" / Int32ub,
                "original_field_record_number" / Int32ub,
                "trace_number_within_field_record" / Int32ub,
                "energy_source_point" / Int32ub,
                "ensemble_number" / Int32ub,
                "trace_number_within_ensemble" / Int32ub,
                "trace_identification_code" / Int16ub,
                "number_of_vertically_summed_traces" / Int16ub,
                "number_of_horizontally_stacked_traces" / Int16ub,
                "data_use" / Int16ub,
                "source_receiver_offset" / Int32ub,
                "receiver_group_elevation" / Int32ub,
                "surface_elevation_at_source" / Int32ub,
                "source_depth_below_surface" / Int32ub,
                "datum_elevation_at_receiver_group" / Int32ub,
                "datum_elevation_at_source" / Int32ub,
                "water_depth_at_source" / Int32ub,
                "water_depth_at_receiver_group" / Int32ub,
                "scalar_for_elevations" / Int16sb,
                "scalar_for_coordinates" / Int16sb,
                "source_coordinate_x" / Int32ub,
                "source_coordinate_y" / Int32ub,
                "group_coordinate_x" / Int32ub,
                "group_coordinate_y" / Int32ub,
                "coordinate_units" / Int16ub,
                "weathering_velocity" / Int16ub,
                "subweathering_velocity" / Int16ub,
                "uphole_time_at_source" / Int16ub,
                "uphole_time_at_group" / Int16ub,
                "source_static_correction" / Int16ub,
                "group_static_correction" / Int16ub,
                "total_static_applied" / Int16ub,
                "lag_time_A" / Int16ub,
                "lag_time_B" / Int16ub,
                "delay_recording_time" / Int16ub,
                "mute_time_start" / Int16ub,
                "mute_time_end" / Int16ub,
                "number_of_samples_in_this_trace" / Int16ub,
                "sample_interval_in_this_trace" / Int16ub,
                None / Bytes(240 - 118),
            ),
            "samples" / Debugger(Array(lambda this: this.header.number_of_samples_in_this_trace, Float32b)),
        )
    )
)
if __name__ == "__main__":
    segy_data = open('../../data/Line_001.sgy', 'rb').read()
    parsed_data = segy_format.parse(segy_data)
    print("EBCDIC Header:")
    print(parsed_data['EBCDIC'])
    print("\nBinary Header:")
    print(parsed_data['binary_header'])
    
    # Add debug info
    print("\nFile size:", len(segy_data))
    print("Number of traces found:", len(parsed_data['traces']))
    
    # Calculate expected size
    binary_header = parsed_data['binary_header']
    samples_per_trace = binary_header.number_of_samples_per_trace
    bytes_per_sample = 4  # assuming 4 bytes for IBM float
    expected_trace_size = 240 + (samples_per_trace * bytes_per_sample)  # 240 for trace header
    expected_total_size = 3600 + (expected_trace_size * binary_header.number_of_data_traces_per_ensemble)
    print("\nExpected file size:", expected_total_size)
    print("Samples per trace:", samples_per_trace)
    print("Expected trace size:", expected_trace_size)
    
    if len(parsed_data['traces']) > 0:
        print("\nFirst trace header:")
        print(parsed_data['traces'][0]['trace_header'])
