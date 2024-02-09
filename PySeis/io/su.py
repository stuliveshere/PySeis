# Standard library imports
from dataclasses import dataclass, field
import os
from pprint import pprint

# Third-party library imports
import numpy as np
import yaml
from typing import List, Dict, Any
import hexdump

# Local application/library specific imports
from .models import create_block_dataclass

class SU(SeisFile):
    """
    Base class for initializing SU files
    """

    def __init__(self):
        super().__init__()
        #this loads the header dictionaries
        self.initialize()
        
        self.channel_sets = [] # A channel set is a list of records
        self.general_headers = []  # segds have general headers

    def initialize(self):
        # self.block_descriptions is a dictionary which will contain the header
        #  and data block definitions for all defined blocks
        self.block_definitions = {}
        self.block_class = {}
        self.load_header_definitions()

