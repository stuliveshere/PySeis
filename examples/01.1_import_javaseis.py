import os
import sys
import numpy as np
import pandas as pd
sys.path.append("/misc/softwareStor/sfletcher/git/PySeis")

from pyseis.io.javaseis.javaseis import JavaSeis as js
from pyseis.io.javaseis.xml_io import JavaSeisXML

path_to_javaseis = "../data/javaseis/"

# Load dataset
dataset = js()
dataset.load(path_to_javaseis)

# Get dimensions from FileProperties
fp_tree = dataset.xml['FileProperties']
axis_lengths = [int(x) for x in JavaSeisXML.get(fp_tree, 'AxisLengths').split()]
nsamples, ntraces, nframes = axis_lengths

# Load all headers into DataFrame
all_headers = []
all_traces = []
for frame in range(nframes):
    headers = dataset.get_headers(frame * ntraces, ntraces)
    traces = dataset.get_traces(frame * ntraces, ntraces)
    all_headers.extend(headers)
    all_traces.extend(traces)

header_df = pd.DataFrame(all_headers)
trace_df = pd.DataFrame(all_traces)

print("\nHeader Statistics:")
print(header_df.describe())

print("\nTrace Statistics:")
print(f"Shape: {trace_df.shape}")
print(trace_df.T.describe())  # Transpose so each row is a trace


