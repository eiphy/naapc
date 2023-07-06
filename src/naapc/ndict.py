from __future__ import annotations
import yaml

import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union, Callable
from .stop_conditions import generate_depth_stop_condition
from .dict_traverse import traverse


class ndict:
    """Due to the internal mechanism, modifications of the raw_dict will not be applied on the
    object."""

    _missing_methods = ["ignore", "false", "error"]

    def __init__(self, d: Optional[Union[ndict, dict]] = None, delimiter: str = ";") -> None:
        assert isinstance(delimiter, str), f"delimiter must be str, but recieved {type(delimiter)}"
        self._delimiter = delimiter

        if isinstance(d, ndict):
            self._d = d.dict
            self._flatten_dict = d.flatten_dict
            if self._delimiter != d._delimiter:
                self.set_delimiter(self._delimiter, d._delimiter)
        elif d is None:
            self._d = {}
            self._flatten_dict = {}
        elif isinstance(d, dict):
            self._d = {}
            self._flatten_dict = {}

            # If v is a dictionary, then it will be flattened when the __setitem__ method tries to get the subtree
            # flatten dictionary recursively.
            for k, v in d.items():
                self._d[k] = v
        else:
            raise TypeError(f"Unexpected type {type(d)}.")

    @property
    def dict(self) -> dict:
        return self._d

    @property
    def flatten_dict(self) -> dict[str, Any]:
        return self._flatten_dict

    def set_delimiter(self, delimiter: str, old_delimiter: Optional[str] = None) -> None:
        old_delimiter = old_delimiter or self._delimiter
        self._delimiter = delimiter
        flatten_dict = {}
        for p, v in self._flatten_dict.items():
            p.replace(old_delimiter, delimiter)
            flatten_dict[p] = v

    def __getitem__(self, path: str) -> None:
        try:
            return self._get_node(path)
        except KeyError as e:
            print(f"Cannot find path {path}")
            raise e

    def __delitem__(self, path: str) -> None:
        path_list = path.split(self._delimiter)
        d = self._get_node(path_list[:-1])
        del d[path_list[-1]]
        for k in self._flatten_dict.keys():
            if k.startswith(path):
                del self._flatten_dict[path]

    def __setitem__(self, path: str, value: Any) -> None:
        assert isinstance(path, str), f"Path can only be str, recieved {type(path)}."

        # Delete old node and flatten dict.
        del self[path]

        # Set new value.
        path_list = path.split(self._delimiter)
        d = self._get_node(path_list[:-1])
        d[path_list[-1]] = value

        # Add new flatten dict.
        if isinstance(value, dict):
            for p, v in ndict(value).flatten_dict:
                tmp_p = ";".join([path, p])
                assert tmp_p not in self._flatten_dict
                self._flatten_dict[tmp_p] = v
        else:
            self._flatten_dict[path] = value

    def __len__(self) -> int:
        return len(self.flatten_dict)

    def __bool__(self) -> bool:
        return bool(len(self) > 0)

    def __contains__(self, path: str) -> bool:
        return bool(path in self.flatten_dict)

    def __str__(self) -> str:
        return yaml.dump(self.dict, sort_keys=False, indent=2)

    def _get_node(self, path: Union[str, list[str]]) -> Any:
        """Return the value of a particular path.

        Return
            Node value. If the node is a dictionary, __class__(node) will be returned.
        """
        if not isinstance(path, list):
            assert isinstance(path, str), f"Path can only be str, recieved {type(path)}."
            path = path.split(self._delimiter)
        v = reduce(getitem, path, self._d)
        return self.__class__(v) if isinstance(v, dict) else v

    def _flatten(self) -> dict[str, Any]:
        def flatten_action(tree: ndict, res: dict, node: Any, path: str, depth: int) -> None:
            if not isinstance(node, dict):
                res[path] = node

        res = {}
        traverse(res, flatten_action)
        return res
