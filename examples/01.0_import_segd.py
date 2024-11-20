import os
import sys
sys.path.append("/misc/softwareStor/sfletcher/git/PySeis")

from pyseis.io.segd.segd import SegD

# Example 1: Read existing file
reader = SegD("../data/00016239.segd")
print(reader.data)

# print("Headers from existing file:")
# print(reader.headers.general_header1)
# print("\nTraces from existing file:")
# for i, trace in enumerate(reader.traces.traces):
#     print(f"Trace {i+1}:")
#     print(f"  Scan Type: {trace.demux_header.scan_type_number}")
#     print(f"  Channel Set: {trace.demux_header.channel_set_number}")
#     print(f"  Trace Number: {trace.demux_header.trace_number}")
#     print(f"  Data shape: {trace.trace_data.shape}")
# print(reader.traces.traces[0])
# print()

# # Example 2: Create new SmartSolo file
# config = SegDConfig(
#     extended_headers=32,
#     external_headers=32,
#     channel_sets=[
#         ChannelSetConfig(
#             number=1,
#             traces=1000,
#             scan_type=1,
#             start_time=0.0,
#             end_time=2000.0,
#             trace_header_extensions=3,
#             sensor_type=2
#         )
#     ]
# )

# writer = SegD(format_type='smartsolo10', config=config)
# writer.write("../data/new_smartsolo.segd")
# print("\nCreated new SmartSolo file: new_smartsolo.segd")