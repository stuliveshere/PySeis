from dataclasses import dataclass
from typing import Dict
from .block import Block
from .decoders import DECODERS

def create_block_dataclass(block_definition: dict):
    """
    Extends a dataclass based on a dictionary of block definitions.
    """
    largest_start_byte_definition = max(block_definition['definition'].values(), key=lambda x: x['start_byte'])
    num_bytes = largest_start_byte_definition['start_byte'] + largest_start_byte_definition['num_bytes']

    class_dict = {
        'payload': block_definition.get('payload', b''),
        'label': block_definition.get('label', ''),
        'definition': block_definition,
        'num_bytes': num_bytes,
        'block_id': block_definition.get('blockID', ''),
        'filename': block_definition.get('filename', ''),
    }

    class_name = ''.join(word.capitalize() for word in class_dict['label'].split())
    if not class_name:
        class_name = 'BlockDataClass'

    for def_name in block_definition['definition'].keys():
        data_format = block_definition['definition'][def_name]['format']
        format_functions = DECODERS.get(data_format)

        if format_functions:
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
            raise ValueError(fUnknown data_format {data_format} for block {def_name})

    blockDataClass = type(class_name, (Block,), class_dict)
    return dataclass(blockDataClass)

