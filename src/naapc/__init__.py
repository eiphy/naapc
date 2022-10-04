from typing import Union

from .nconfig import CustomArgs, NConfig
from .ndict import NDict

NestedOrDict = Union[NConfig, NDict, dict]

__version__ = "1.2.0"
