from dataclasses import dataclass, field
from typing import List, Optional, Set

from datafiles import datafile
from datafiles.converters import String

@datafile("../tmp/sample.json", manual=True)
class SampleAsJSON:
    bool_: bool
    int_: int
    float_: float
    str_: str

@dataclass
class _NestedSample1:
    name: str
    score: float


@dataclass(frozen=True)
class _FrozenNestedSample1:
    name: str
    score: float


@dataclass
class _NestedSample2:
    name: str = "b"
    score: float = 3.4



@dataclass
class _NestedSample3:
    name: str
    score: float
    weight: Optional[int]

