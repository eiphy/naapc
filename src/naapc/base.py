from __future__ import annotations

import json
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
        assert delimiter is None or isinstance(
            delimiter, (str)
        ), f"delimiter must be str, but recieved {type(delimiter)}"

        # Public attributes
        self.return_nested = return_nested
        self._delimiter = delimiter or self.DEFAULT_DELIMITER

        self._d = {}
        if d is not None:
            if isinstance(d, NestedBase):
                self.load_states(d.states())
            elif isinstance(d, dict):
                self._init_from_dict(d)
            else:
                raise TypeError(f"Unexpected type: {type(d)}!")

    @classmethod
    def from_states(
        cls,
        states: Optional[dict] = None,
        d: Optional[dict] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ) -> NestedBase:
        if states is None:
            assert d is not None and delimiter
            states = {"dict": d, "delimiter": delimiter}
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

    @property
    def flatten_dict(self) -> dict:
        return self._get_flatten_dict()

    def __getitem__(self, key: Union[str, int]) -> Any:
        path = key if isinstance(key, str) else list(self.keys())[key]
        return self._dict_nested_conversion_before_return(path, self._get_node(path))

    # Option to prevent overwriting.
    def __setitem__(self, path: str, value: Any) -> Any:
        if isinstance(value, dict):
            value = self.__class__(d=value, delimiter=self._delimiter).dict
        elif isinstance(value, NestedBase):
            value = value.dict
        elif isinstance(value, (list, tuple, set)):
            value = value.__class__(
                [
                    self.__class__(d=x).dict if isinstance(x, (NestedBase, dict)) else x
                    for x in value
                ]
            )

        if self._delimiter not in path:
            self._d[path] = value
        else:
            path_list = path.split(self._delimiter)
            v = self._d
            for node in path_list[:-1]:
                if node not in v or not isinstance(v[node], dict):
                    v[node] = {}
                v = v[node]
            v[path_list[-1]] = value

    def __delitem__(self, path: str) -> None:
        if self.delimiter not in path:
            del self._d[path]
            return
        path_list = path.split(self._delimiter)
        parent = self._get_node(path_list[:-1])
        del parent[path_list[-1]]

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
        return self.dict == self.__class__(other).dict

    def __str__(self) -> str:
        return yaml.dump(self.dict, sort_keys=False, indent=2)

    def __repr__(self) -> str:
        return f"<Nested dictionary of {len(self)} subtrees.>: {self.dict}"

    def json(self, indent=2, sort_keys=False) -> str:
        return json.dumps(self._d, indent=indent, sort_keys=sort_keys)

    def states(self) -> dict:
        """Subclasses may provide more attributes."""
        return {"dict": self.dict, "delimiter": self.delimiter}

    def load_states(self, states: dict) -> NestedBase:
        self._d = states["dict"]
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

    def update(self, d: Union[dict, NestedBase]) -> None:
        flatten_dict = self.__class__(d).flatten_dict
        for p, v in flatten_dict.items():
            self[p] = v

    def size(self, max_depth: int = 1, ignore_none: bool = False) -> int:
        def _size_action(tree: dict, res: list[int], node: Any, path: str, depth: int):
            if (
                path is not None
                and (not isinstance(node, dict) or depth == max_depth)
                and (not ignore_none or ignore_none and node is not None)
            ):
                res[0] += 1

        res = [0]
        traverse(tree=self.dict, res=res, actions=_size_action, depth=max_depth)
        return res[0]

    def diff(self, d: Union[NestedBase, dict]) -> dict[str, tuple[Any, Any]]:
        """Compare the leaves."""
        d = self.__class__(d)
        d_flatten_dict = d.flatten_dict
        res = {}
        for p, v1 in self.flatten_dict.items():
            if p not in d_flatten_dict:
                res[p] = (v1, None)
            elif v1 != d[p]:
                res[p] = (v1, d[p])
        res.update({p: (None, v) for p, v in d_flatten_dict.items() if p not in self})
        return res

    def _get_flatten_dict(self) -> dict[str, Any]:
        def flatten_action(tree: dict, res: dict, node: Any, path: str, depth: int) -> None:
            if (path is not None) and (not isinstance(node, dict) or not node):
                path = path.replace(";", self._delimiter)
                res[path] = node

        res = {}
        traverse(self.dict, res, flatten_action)
        return res

    def _init_from_dict(self, d: dict) -> None:
        for k, v in d.items():
            self[k] = v

    def _get_node(self, path: Union[list[str], str]) -> Any:
        """Return the value of a particular path.

        Return
            Node value. If the node is a dictionary, __class__(node) will be returned.
        """
        path_list = path if isinstance(path, list) else path.split(self.delimiter)
        return reduce(getitem, path_list, self._d)

    def _dict_nested_conversion_before_return(self, path: str, val: Any) -> Any:
        return (
            self.__class__.from_states(d=val, delimiter=self.delimiter, **self.configs)
            if self.return_nested and isinstance(val, dict)
            else val
        )
