# Standard library imports
from dataclasses import dataclass, field
from pprint import pprint
import os

# Third-party library imports
import numpy as np
from typing import List, Dict, Any

# Local application/library specific imports
from .models import SeisFile, create_block_dataclass

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
        #absolute path the yaml file.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_file = os.path.join(current_dir, 'su.yaml')
        self.load_header_definitions([yaml_file])

if __name__ == "__main__":
    su = SU()