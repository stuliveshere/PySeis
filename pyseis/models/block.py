from dataclasses import dataclass
from typing import Dict, Any
from pprint import pprint
import hexdump

@dataclass
class Block:
    """
    Fundamental unit of seismic data storage
    can be a header block or a data block
    """
    payload: bytes = b''
    label: str = ''
    definition: Dict[str, Any] = None
    num_bytes: int = 0
    block_id: str = ''
    filename: str = ''

    def summary(self):
        print(f---- {self.__class__.__name__} ----)
        for key, value in vars(self).items():
            print(f{key}: {value})
        for key in self.definition.keys():
            if key != 'definition':
                print(f{key}: {self.definition[key]})
        contents = {def_name: getattr(self, def_name, None) for def_name in self.definition['definition'].keys()}
        pprint(contents, sort_dicts=False)

    def hex(self):
        return hexdump.dump(self.payload)

    def load(self, filemap, offset):
        self.payload = filemap[offset:offset+self.num_bytes]

    def __del__(self):
        if hasattr(self, 'mmap'):
            self.payload.close()

