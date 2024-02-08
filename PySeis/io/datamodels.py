# methods.py

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pprint import pprint
from .decoders import DECODERS
import os
import yaml, hexdump
import pdb
import numpy as np

@dataclass
class Block:
    """
    Fundamental unit of seismic data storage
    can be a header block or a data block

    The class variables are initialized by the create_block_dataclass factory function.
    this factory function sets the class attributes based upon the yaml definition
    and links the getter and setter functions.
    """
    def summary(self):
        print(f"---- {self.__class__.__name__} ----")
        
        # Iterating over all class attributes
        for key, value in vars(self).items():
            print(f"{key}: {value}")

        for key in self.definition.keys():
            if key != 'definition':
                print("%s: %s"%(key, self.definition[key]))

        contents = {}
        for def_name in self.definition['definition'].keys():
            contents[def_name] = getattr(self, def_name, None)
        pprint(contents, sort_dicts=False)
    
    def hex(self):
        return hexdump.dump(self.data)
    
    def load(self, filemap, offset):
        self.payload = filemap[offset:offset+self.num_bytes]

    def __del__(self):
        if hasattr(self, 'mmap'):
            self.payload.close()


@dataclass
class Trace:
    """
    A trace object can consist of multiple header blocks
    and a data block
    """
    headers: List[Block] = field(default_factory=list)  # List of trace header blocks
    data: Block = None  # Trace data block

    def summary(self):
        print(f"---- {self.__class__.__name__} ----")
        for header in self.headers:
            if hasattr(header, 'summary'):
                header.summary()
        if hasattr(self.data, 'summary'):
            self.data.summary()

@dataclass 
class Record:
    """
    A record can consist of multiple generic header objects, and multiple
    trace objects.
    """
    headers: List[Block] = field(default_factory=list)  # List of header blocks
    traces: List[Trace] = field(default_factory=list)  # List of traces
    
    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self.traces):
            result = self.traces[self._index]
            self._index += 1
            return result
        else:
            raise StopIteration
            
    def summary(self):
        print(f"---- {self.__class__.__name__} ----")
        for header in self.headers:
            if hasattr(header, 'summary'):
                header.summary()
        for trace in self.traces:
            if hasattr(trace, 'summary'):
                trace.summary()

@dataclass
class SeisFile:
    """
    Represents a seismic file consisting of one or more records.
    Provides generic methods common to all seismic files.
    """
    
    # Paths to the definition files
    definition_paths: str = '../definitions'
    
    def initialize(self):
        # self.block_descriptions is a dictionary which will contain the header
        #  and data block definitions for all defined blocks
        self.block_definitions = {}
        self.block_class = {}
        self.load_header_definitions()

    def map(self, filename):
        return np.memmap(filename, dtype='uint8', mode='r')


    def load_header_definitions(self):
        """
        A generic method which loads header definitions
        from yaml files
        """
        yaml_path = os.path.join(os.getcwd(), self.definition_paths)
        for yml_file in os.listdir(yaml_path):
            if "yml" in yml_file or "yaml" in yml_file:
                with open(os.path.join(yaml_path, yml_file), 'r') as f:
                    self.block_definitions.update(yaml.safe_load(f))
        
        for key in self.block_definitions:
            self.block_class[key] = create_block_dataclass(self.block_definitions[key])

def create_block_dataclass(block_definition: dict):
    """
    Extends a dataclass based on a dictionary of block definitions.

    Each block definition should be a dictionary with the required fields.
    """

    # Calculate num_bytes from the entry with the largest start_byte 
    largest_start_byte_definition = max(block_definition['definition'].values(), key=lambda x: x['start_byte'])
    num_bytes = largest_start_byte_definition['start_byte'] + largest_start_byte_definition['num_bytes']


    # Create the class dictionary with default values
    class_dict = {
        'payload': block_definition.get('payload', b''),
        'label': block_definition.get('label', ''),
        'definition': block_definition,
        'num_bytes': num_bytes,
        'block_id': block_definition.get('blockID', ''),
        'filename': block_definition.get('filename', ''),
    }

    # Convert label to a valid Python class name
    class_name = "".join(word.capitalize() for word in class_dict['label'].split())
    if not class_name:
        class_name = 'BlockDataClass'  # default name if label is empty

    for def_name in block_definition['definition'].keys():
        data_format = block_definition['definition'][def_name]['format']
        format_functions = DECODERS.get(data_format)
            
        if format_functions:
            # Create generalized getter and setter. all set/get functions will need to access instance variables for parameters
            def make_getter(format_func, def_name):
                def getter(self):
                    return format_func(self, def_name)
                return getter

            def make_setter(format_func, def_name):
                def setter(self, value):
                    format_func(self, def_name, value)
                return setter

            getter_func = make_getter(format_functions['get'], def_name)
            setter_func = make_setter(format_functions['set'], def_name)
            class_dict[def_name] = property(getter_func, setter_func)

        else:
            raise ValueError(f"Unknown data_format '{data_format}' for block '{def_name}'")
            

    # Create the dataclass
    blockDataClass = type((class_name), (Block,), class_dict)

    return dataclass(blockDataClass)

