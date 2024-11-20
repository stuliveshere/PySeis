from construct import *
from ..adapters import *


# Define SmartSolo-specific structures
smartsolo_extended_header = Struct(
    "acquisition_length" / Int32ub,          # Bytes 1-4
    "sample_rate" / Int32ub,                 # Bytes 5-8
    "total_number_of_traces" / Int32ub,      # Bytes 9-12
    "number_of_auxes" / Int32ub,             # Bytes 13-16
    "number_of_seis_traces" / Int32ub,       # Bytes 17-20
    "number_of_dead_seis_traces" / Int32ub,  # Bytes 21-24
    "number_of_live_seis_traces" / Int32ub,  # Bytes 25-28
    "type_of_source" / Int32ub,              # Bytes 29-32
    "number_of_samples_in_trace" / Int32ub,  # Bytes 33-36
    "shot_number" / Int32ub,                 # Bytes 37-40
    "time_break_window" / Float32b,          # Bytes 41-44
    "test_record_type" / Int32ub,            # Bytes 45-48
    "spread_first_line" / Int32ub,           # Bytes 49-52
    "spread_first_number" / Int32ub,         # Bytes 53-56
    "spread_number" / Int32ub,               # Bytes 57-60  # [Added Missing Field]
    "spread_type" / Int32ub,                 # Bytes 61-64
    "time_break" / Int32ub,                  # Bytes 65-68
    "uphole_time" / Int32ub,                 # Bytes 69-72
    "blaster_id" / Int32ub,                  # Bytes 73-76
    "blaster_status" / Int32ub,              # Bytes 77-80
    "refraction_delay" / Int32ub,            # Bytes 81-84
    "tb_to_t0" / Int32ub,                    # Bytes 85-88
    "internal_time_break" / Int32ub,         # Bytes 89-92
    "prestack_within_field_units" / Int32ub, # Bytes 93-96
    "noise_elimination_type" / Int32ub,      # Bytes 97-100
    "low_trace_percentage" / Int32ub,        # Bytes 101-104
    "low_trace_value" / Int32ub,             # Bytes 105-108
    "number_of_windows" / Int32ub,           # Bytes 109-112
    "historic_editing_type" / Int32ub,       # Bytes 113-116
    "noisy_trace_percentage" / Int32ub,      # Bytes 117-120
    "historic_range" / Int32ub,              # Bytes 121-124
    "historic_taper_length" / Int32ub,       # Bytes 125-128
    "threshold" / Int32ub,                   # Bytes 129-132
    "historic_zeroing_length" / Int32ub,     # Bytes 133-136
    "type_of_process" / Int32ub,             # Bytes 137-140
    "acquisition_type_tables" / Bytes(128),  # Bytes 141-268
    "threshold_type_tables" / Bytes(128),    # Bytes 269-396
    "stacking_fold" / Int32ub,               # Bytes 397-400
    "not_used" / Bytes(80),                  # Bytes 401-480
    "record_length" / Int32ub,               # Bytes 481-484
    "autocorrelation_peak_time" / Int32ub,   # Bytes 485-488
    "not_used_2" / Bytes(4),                 # Bytes 489-492
    "correlation_pilot_number" / Int32ub,    # Bytes 493-496
    "pilot_length" / Int32ub,                # Bytes 497-500
    "sweep_length" / Int32ub,                # Bytes 501-504
    "acquisition_number" / Int32ub,          # Bytes 505-508
    "max_of_max_aux" / Float32b,             # Bytes 509-512
    "max_of_max_seis" / Float32b,            # Bytes 513-516
    "dump_stacking_fold" / Int32ub,          # Bytes 517-520
    "tape_label" / PaddedString(16, 'ascii'),# Bytes 521-536
    "tape_number" / Int32ub,                 # Bytes 537-540
    "software_version" / PaddedString(16, 'ascii'), # Bytes 541-556
    "date" / PaddedString(12, 'ascii'),      # Bytes 557-568
    "source_easting" / Float64b,             # Bytes 569-576
    "source_northing" / Float64b,            # Bytes 577-584
    "source_elevation" / Float32b,           # Bytes 585-588
    "slip_sweep_mode_used" / Int32ub,        # Bytes 589-592
    "files_per_tape" / Int32ub,              # Bytes 593-596
    "file_count" / Int32ub,                  # Bytes 597-600
    "acquisition_error_description" / PaddedString(160, 'ascii'), # Bytes 601-760
    "filter_type" / Int32ub,                 # Bytes 761-764
    "stack_is_dumped" / Int32ub,             # Bytes 765-768
    "stack_sign" / Int32ub,                  # Bytes 769-772
    "tilt_correction_used" / Int32ub,        # Bytes 773-776
    "swath_name" / PaddedString(64, 'ascii'),# Bytes 777-840
    "operating_mode" / Int32ub,              # Bytes 841-844
    "undefined1" / Int32ub,                  # Bytes 845-848
    "no_log" / Int32ub,                      # Bytes 849-852
    "listening_time" / Int32ub,              # Bytes 853-856
    "type_of_dump" / Int32ub,                # Bytes 857-860
    "undefined2" / Int32ub,                  # Bytes 861-864
    "swath_id" / Int32ub,                    # Bytes 865-868
    "trace_offset_removed" / Int32ub,        # Bytes 869-872
    "gps_time_break" / Int64ub,              # Bytes 873-880
    "aligned_gps_time_break" / Int64ub,      # Bytes 881-888
    "undefined3" / Bytes(136),               # Bytes 893-1024
)

smartsolo_external_header = Struct(
    "field_file_number" / Int32ub,
    "file_number" / Int32ub,
    "undefined" / Bytes(1016),
)


smartsolo_trace_header_extension2 = Struct(
    "receiver_point_easting" / Float64b,
    "receiver_point_northing" / Float64b,
    "receiver_point_elevation" / Float32b,
    "sensor_type_number" / Int8ub,
    "undefined" / Bytes(3),
    "dsd_identification_number" / Int32ub,
    "extended_trace_number" / Int32ub,
)

smartsolo_trace_header_extension3 = Struct(
    "gps_time_break" / Int64ub,
    "time_break_offset" / Int16ub,
    "undefined" / Bytes(22),
)


