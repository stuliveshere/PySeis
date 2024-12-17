import os
import sys
import numpy as np
import pandas as pd
sys.path.append("/misc/softwareStor/sfletcher/git/PySeis")

from pyseis.io.javaseis.javaseis import JavaSeis as js
from pyseis.io.javaseis.xml_io import JavaSeisXML

path_to_javaseis = "../data/javaseis/"

# Create new dataset
dataset = js()
dataset.create_new()

# Add headers
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

# Print the updated XML
JavaSeisXML.print_contents(dataset.xml['FileProperties'])
