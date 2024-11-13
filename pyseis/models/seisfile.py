from dataclasses import dataclass
from typing import Dict
import numpy as np
import yaml
from .factory import create_block_dataclass

@dataclass
class SeisFile:
    """
    Represents a seismic file consisting of one or more records.
    Provides generic methods common to all seismic files.
    """
    definition_paths: str = '../definitions'
    block_definitions: Dict[str, dict] = None
    block_class: Dict[str, type] = None

    def initialize(self):
        self.block_definitions = {}
        self.block_class = {}
        self.load_header_definitions()

    def map(self, filename):
        return np.memmap(filename, dtype='uint8', mode='r')

    def load_header_definitions(self, yml_files):
        for yml_file in yml_files:
            with open(yml_file, 'r') as f:
                self.block_definitions.update(yaml.safe_load(f))
        for key in self.block_definitions:
            self.block_class[key] = create_block_dataclass(self.block_definitions[key])

