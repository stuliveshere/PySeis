from dataclasses import dataclass, field
from typing import List
from .block import Block

@dataclass
class Trace:
    """
    A trace object can consist of multiple header blocks
    and a data block
    """
    headers: List[Block] = field(default_factory=list)
    data: Block = None

    def summary(self):
        print(f---- {self.__class__.__name__} ----)
        for header in self.headers:
            if hasattr(header, 'summary'):
                header.summary()
        if hasattr(self.data, 'summary'):
            self.data.summary()

