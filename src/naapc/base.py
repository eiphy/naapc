from __future__ import annotations

from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union

import yaml

from .dict_traverse import traverse


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
                self.load_states(d.states())
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

    @classmethod
    def from_states(cls, states: dict, return_nested: bool = True) -> NestedBase:
        return cls(return_nested=return_nested).load_states(states)

    @abstractproperty
    def raw_is_plain(self) -> bool:
        ...

    @property
    def paths(self) -> list[str]:
        """Get all possible paths."""

        def _path_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            if path is not None:
                res.append(path)

        res = []
        traverse(tree=self.dict, res=res, actions=_path_action)
        return res

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
        return self._dict_nested_conversion_before_return(path, self._get_node(path))

    def __len__(self) -> int:
        return len(self._d)

    def __bool__(self) -> bool:
        return bool(self._d)

    def __contains__(self, path: str) -> bool:
        nodes = path.split(self._delimiter)
        d = self.dict
        for n in nodes:
            if n not in d:
                return False
            d = d[n]
        return True

    def __eq__(self, other: Union[dict, NestedBase]) -> bool:
        other = other.dict if isinstance(other, NestedBase) else other
        return self._d == other

    def __str__(self) -> str:
        return yaml.dump(self.dict, sort_keys=False, indent=2)

    def __repr__(self) -> str:
        return f"<Nested dictionary of {len(self)} subtrees.>: {self.dict}"

    def states(self) -> dict:
        """Subclasses may provide more attributes."""
        return {"dict": self.dict, "delimiter": self.delimiter}

    def load_states(self, states: dict) -> NestedBase:
        self._d = states["dict"]
        self.delimiter = states["delimiter"]
        return self

    # TODO: Make it a generator.
    def keys(self, max_depth: int = 1) -> list[str]:
        """Return a list of leave and depth <= depth"""

        def _keys_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            if path is not None and (not isinstance(node, dict) or depth == max_depth):
                res.append(path)

        if max_depth == 1:
            return list(self._d.keys())

        res = []
        traverse(tree=self._d, res=res, actions=_keys_action, depth=max_depth)
        return res

    # TODO: Make it a generator.
    def values(self, max_depth: int = 1) -> list[Any]:
        def _values_action(tree: dict, res: list[Any], node: Any, path: str, depth: int):
            if path is not None and (not isinstance(node, dict) or depth == max_depth):
                res.append(self._dict_nested_conversion_before_return(path, node))

        res = []
        traverse(tree=self._d, res=res, actions=_values_action, depth=max_depth)
        return res

    # TODO: Make it a generator.
    def items(self, max_depth: int = 1) -> list[tuple[str, Any]]:
        return list(zip(self.keys(max_depth=max_depth), self.values(max_depth=max_depth)))

    def get(self, key: Union[str, int], default: Any = None) -> Any:
        path = key if isinstance(key, str) else list(self.keys())[key]
        try:
            return self[path]
        except KeyError:
            return default

    def _init_from_dict(self, d: dict) -> None:
        self._d = d

    def _get_node(self, path: Union[list[str], str]) -> Any:
        """Return the value of a particular path.

        Return
            Node value. If the node is a dictionary, __class__(node) will be returned.
        """
        path_list = path if isinstance(path, list) else path.split(self.delimiter)
        return reduce(getitem, path_list, self._d)

    def _dict_nested_conversion_before_return(self, path: str, val: Any) -> Any:
        return (
            self.__class__(d=val, delimiter=self.delimiter, **self.configs)
            if self.return_nested and isinstance(val, dict)
            else val
        )
