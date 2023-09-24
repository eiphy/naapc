from __future__ import annotations

from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union


class NestedBase(ABC):
    DEFAULT_DELIMITER = ";"

    def __init__(
        self,
        d: Optional[Union[dict, NestedBase]] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ):
        assert isinstance(delimiter, str), f"delimiter must be str, but recieved {type(delimiter)}"

        # Public attributes
        self.return_nested = return_nested
        self.delimiter = delimiter or self.DEFAULT_DELIMITER

        self._d = {}
        if d is not None:
            if isinstance(d, NestedBase):
                self.load_data(d.data())
            elif isinstance(d, dict):
                self._init_from_dict(d)
            else:
                raise TypeError(f"Unexpected type: {type(d)}!")

    @classmethod
    def fast_init(
        cls,
        d: Optional[Union[dict, NestedBase]] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ):
        """Fast initialization by assume certain data conditions."""
        return cls(d=d, delimiter=delimiter, return_nested=return_nested)

    @abstractproperty
    def raw_is_plain(self) -> bool:
        ...

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: str) -> None:
        self._delimiter = delimiter

    @property
    def return_nested(self) -> bool:
        return self._return_nested

    @return_nested.setter
    def return_nested(self, value: bool) -> None:
        self._return_nested = bool(value)

    @property
    def dict(self) -> dict:
        return self._d

    @property
    def configs(self) -> dict:
        return {"return_nested": self.return_nested}

    def __getitem__(self, key: Union[str, int]) -> Any:
        path = key if isinstance(key, str) else list(self.keys())[key]
        return self._dict_nested_conversion_before_return(self._get_node(path))

    def __len__(self) -> int:
        return len(self._d)

    def __bool__(self) -> bool:
        return bool(self._d)

    def data(self) -> dict:
        """Subclasses may provide more attributes."""
        return {"dict": self.dict, "delimiter": self.delimiter}

    def load_data(self, states: dict) -> NestedBase:
        self._d = states["dict"]
        self.delimiter = states["delimiter"]
        return self

    def _init_from_dict(self, d: dict) -> None:
        self._d = d

    def _get_node(self, path: Union[list[str], str]) -> Any:
        """Return the value of a particular path.

        Return
            Node value. If the node is a dictionary, __class__(node) will be returned.
        """
        path_list = path if isinstance(path, list) else path.split(self.delimiter)
        return reduce(getitem, path_list, self._d)

    def _dict_nested_conversion_before_return(self, val: Any) -> Any:
        return (
            self.__class__(d=val, delimiter=self.delimiter, **self.configs)
            if self.return_nested and isinstance(val, dict)
            else val
        )
