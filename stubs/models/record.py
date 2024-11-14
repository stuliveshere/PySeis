from dataclasses import dataclass, field
from typing import List
from .block import Block
from .trace import Trace

@dataclass
class Record:
    """
    A record can consist of multiple generic header objects, and multiple
    trace objects.
    """
    headers: List[Block] = field(default_factory=list)
    traces: List[Trace] = field(default_factory=list)

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
        print(f---- {self.__class__.__name__} ----)
        for header in self.headers:
            if hasattr(header, 'summary'):
                header.summary()
        for trace in self.traces:
            if hasattr(trace, 'summary'):
                trace.summary()

