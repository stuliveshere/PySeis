from construct import *
from typing import List
from .formats.segd21 import (
    general_header1,
    general_header2,
    general_header_n,
    channel_set_header,
    demux_header,
    trace_header_extension_format
)
from .formats.smartsolo10 import (
    smartsolo_extended_header,
    smartsolo_external_header,
    smartsolo_trace_header_extension2,
    smartsolo_trace_header_extension3
)
from .adapters import TraceDataAdapter

class SegD21Format:
    """SEG-D file parser using dynamic Construct structures."""

    def __init__(self, filename: str = None):
        self.filename = filename
        self.parsed_data = None
        self.traces_per_channel_set: List[int] = []
        self.samples_per_channelset: List[int] = []

        if filename:
            self.read()

    def read(self):
        """Parse the SEG-D file using dynamic Construct structures."""
        def get_overflow(value1, value2):
            if str(value1).isdigit():
                return value1
            else:
                return value2
        
        # Define helper functions for dynamic field computations
        def get_record_length(ctx):
            return get_overflow(ctx.general_header1.record_length, ctx.general_header2.extended_record_length)

        def get_channel_sets_per_scan_type(ctx):
            return get_overflow(ctx.general_header1.channel_sets_per_scan_type, ctx.general_header2.extended_channel_sets)

        def get_extended_header_blocks(ctx):
            return get_overflow(ctx.general_header1.extended_header_blocks, ctx.general_header2.extended_header_blocks)

        def get_external_header_blocks(ctx):
            return get_overflow(ctx.general_header1.external_header_blocks, ctx.general_header2.external_header_blocks)

        def select_extended_header(ctx):
            if ctx.general_header1.manufacturer_code == 61:
                return smartsolo_extended_header
            else:
                return Array(ctx.extended_header_blocks, Bytes(32))

        def select_external_header(ctx):
            if ctx.general_header1.manufacturer_code == 61:
                return smartsolo_external_header
            else:
                return Array(ctx.external_header_blocks, Bytes(32))

        def select_trace_header_extension(ctx):
            if ctx._.general_header1.manufacturer_code == 61:
                return Struct(
                    "ext1" / trace_header_extension_format,
                    "ext2" / smartsolo_trace_header_extension2,
                    "ext3" / smartsolo_trace_header_extension3,
                    "remaining" / Array(
                        lambda ctx: max(0, ctx._.demux_header.trace_header_extensions - 3),
                        Bytes(32)
                    )
                )
            else:
                return Struct(
                    "ext1" / trace_header_extension_format,
                    "remaining" / Array(
                        lambda ctx: max(0, ctx._.demux_header.trace_header_extensions - 1),
                        Bytes(32)
                    )
                )

        def get_trace_data_struct(ctx):
            """Get the trace data structure based on format code."""
            # Map format codes to data types and sample sizes

            # Get the number of samples per trace
            return Array(
                ctx.trace_header_extensions.ext1.samples_per_trace,
                TraceDataAdapter(Float32b, ctx.general_header1.format_code),
            )

        # Define the top-level SEG-D structure
        segd_file = Struct(
            "general_header1" / general_header1,
            
            "general_header2" / If(this.general_header1.additional_gh_blocks >= 1, general_header2),
            
            "general_headers_n" / If(this.general_header1.additional_gh_blocks > 1,
                Array(this.general_header1.additional_gh_blocks - 1, general_header_n)
            ),
            
            # Compute actual values based on indicators
            "record_length" / Computed(get_record_length),
            "channel_sets_per_scan_type" / Computed(get_channel_sets_per_scan_type),
            "extended_header_blocks" / Computed(get_extended_header_blocks(this)),
            "external_header_blocks" / Computed(get_external_header_blocks(this)),
            
            # Channel set headers
            "channel_set_headers" / Array(
                this.channel_sets_per_scan_type,
                channel_set_header
            ),
            
            # Extended headers
            "extended_headers" / select_extended_header(this),
            
            # External headers
            "external_headers" / select_external_header(this),
            Probe(),
            # Trace data (assuming demultiplexed data)
            "total_traces" / Computed(self.calculate_total_traces),
            "traces" / Array(this.total_traces, Struct(
                "demux_header" / demux_header,
                "trace_header_extensions" / select_trace_header_extension(this),
                "trace_data" / get_trace_data_struct(this),
            ))
        )

        # Parse the SEG-D file
        with open(self.filename, 'rb') as f:
            self.data = segd_file.parse_stream(f)


    def calculate_total_traces(self, ctx):
        """Calculate total number of traces from channel sets."""
        total_traces = 0
        for channel_set in ctx.channel_set_headers:
            total_traces += channel_set.number_of_channels
        return total_traces

    def get_traces_per_channel_set(self):
        """Extract the number of traces per channel set."""
        self.traces_per_channel_set = [cs.number_of_channels for cs in self.parsed_data.channel_set_headers]

    # Accessor methods
    def get_general_header1(self):
        return self.parsed_data.general_header1

    def get_general_header2(self):
        return self.parsed_data.general_header2

    def get_channel_set_headers(self):
        return self.parsed_data.channel_set_headers

    def get_extended_headers(self):
        return self.parsed_data.extended_headers

    def get_external_headers(self):
        return self.parsed_data.external_headers

    def get_traces(self):
        return self.parsed_data.traces
