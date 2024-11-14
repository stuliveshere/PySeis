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

    def __init__(self, path=None):
        super().__init__()
        #this loads the header dictionaries
        self.initialize()
        self.path = path
        if path:
            open(self.path)
 

    def open(self, path):
        pass

if __name__ == "__main__":
    su = SU()