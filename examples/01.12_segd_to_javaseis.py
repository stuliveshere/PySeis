#i'm doing a direct mapping for now. eventually we will want to translate through the seisdata format

import os
import sys
sys.path.append("/misc/softwareStor/sfletcher/git/PySeis")
import numpy as np
from pathlib import Path

from pyseis.io.segd.segd import SegD
from pyseis.io.javaseis.javaseis import JavaSeis as js
from pyseis.io.javaseis.xml_io import JavaSeisXML

path_to_javaseis = "../data/00016239.js"
path_to_segd = "../data/00016239.segd"

# Initialize JavaSeis from first SEGD
segd = SegD(path_to_segd)
nsamples = segd.data.data.traces[0].trace_header_extensions.ext1.samples_per_trace
ntraces = len(segd.data.data.traces)
nframes = 1
traces = segd.data.data.traces

# Create new dataset
dataset = js()
dataset.create_new(nsamples, ntraces, nframes)

# Set data type and keys
fp_tree = dataset.xml["FileProperties"]
JavaSeisXML.set(fp_tree, "DataType", "SOURCE")

# Update axis labels for source data
JavaSeisXML.set(fp_tree, "AxisLabels", ["TIME", "SEQNO", "FRAME"], "string")


# Update CustomProperties
custom_props = fp_tree.find(".//parset[@name='CustomProperties']")
if custom_props is not None:
    JavaSeisXML.set(fp_tree, "PrimaryKey", "FRAME")
    JavaSeisXML.set(fp_tree, "SecondaryKey", "SEQNO")
    JavaSeisXML.set(fp_tree, "PrimarySort", "source")
    JavaSeisXML.set(fp_tree, "Stacked", "false")

# Add headers (without SEQNO since it's already in the template)
dataset.add_header(
    label="FFID",
    description="Field File Identifier",
    format="INTEGER"
)

dataset.add_header(
    label="S_LINE",
    description="Source Line",
    format="INTEGER"
)

dataset.add_header(
    label="SOU_SLOC",
    description="Source Station",
    format="INTEGER"
)

dataset.add_header(
    label="R_LINE",
    description="Receiver Line",
    format="INTEGER"
)

dataset.add_header(
    label="SRF_SLOC",
    description="Receiver Station",
    format="INTEGER"
)

dataset.add_header(
    label="FRAME",
    description="Frame index",
    format="INTEGER"
)

# Create the JavaSeis directory structure
os.makedirs(path_to_javaseis, exist_ok=True)

# Save the XML files
dataset.save(path_to_javaseis)

# Create trace and header data files
header_file = open(os.path.join(path_to_javaseis, "TraceHeaders0"), "wb")
trace_file = open(os.path.join(path_to_javaseis, "TraceFile0"), "wb")

# Write trace headers and data
for i, trace in enumerate(traces):
    # Create header dictionary using general headers
    header = {
        "SEQNO": i + 1,  # Use the existing SEQNO header
        "FFID": segd.data.data.general_headers_n[0].expanded_file_number,
        "S_LINE": segd.data.data.general_headers_n[0].source_line_number_int,
        "SOU_SLOC": segd.data.data.general_headers_n[0].source_point_number_int,
        "R_LINE": trace.trace_header_extensions.ext1.receiver_line_number,
        "SRF_SLOC": trace.trace_header_extensions.ext1.receiver_point_number,
        "FRAME": 1
    }
    
    # Write trace and headers using write_trace
    dataset.write_trace(
        trace_data=np.array(trace.trace_data, dtype=np.float32),
        headers=header,
        trace_file=trace_file,
        header_file=header_file
    )

# Close files
header_file.close()
trace_file.close()

print(f"JavaSeis dataset created at: {path_to_javaseis}")




