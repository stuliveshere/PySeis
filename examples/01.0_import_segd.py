import os
import sys
sys.path.append("/misc/softwareStor/sfletcher/git/PySeis")

from pyseis.io.segd.segd import SegD

# Example 1: Read SEGDs and create JavaSeis
path_to_segd = "../data/00016239.segd"

# Initialize JavaSeis from first SEGD
segd = SegD(path_to_segd)
nsamples = segd.data.data.traces[0].trace_header_extensions.ext1.samples_per_trace
ntraces = len(segd.data.data.traces)
nframes = 1
traces = segd.data.data.traces

