from __future__ import annotations

import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union


class ndict:
    """Due to the internal mechanism, modifications of the raw_dict will not be applied on the
    object."""

    _missing_methods = ["ignore", "false", "error"]

    def __init__(
        self, dictionary: Optional[Union[ndict, dict]] = None, delimiter: str = ";"
    ) -> None:
        dictionary = dictionary or {}
        if isinstance(dictionary, ndict):
            self._d = dictionary.raw_dict
        elif isinstance(dictionary, dict):
            self._d = dictionary
        else:
            raise TypeError(f"Unexpected type {type(dictionary)}.")

        assert isinstance(delimiter, str), f"delimiter must be str, but recieved {type(delimiter)}"
        self.delimiter = delimiter
        self._update_flatten()

    @classmethod
    def from_flatten_dict(cls, flatten_dict: dict, delimiter=";") -> ndict:
        """Generate nested from flattened dictionary.
        The delimiter must be the same!
        """
        nd = cls({}, delimiter=delimiter)
        nd.update(flatten_dict)
        return nd

    @classmethod
    def from_list_of_dict(cls, ls: list, delimiter=";") -> ndict:
        """Generate nested from a list of dictionaries."""
        res = cls()
        for d in ls:
            res.update(d)
        return res

    def is_matched(self, query: dict, missing_method: str = "ignore", **kwargs) -> bool:
        """Test if the dictionary is the queried one.

        Syntax:
            1. Normal path-value pair: {path: value}.
            2. Query expression: {path: !QUERY [python expression returns boolean results]}. The
                expression can use d: the dictionary, path: the query path and any other input
                kwargs.

        Args:
            query (dict): query dictionary.
            missing_method (str): actions when the path is missing from the dictionary. Support:
            ['ignore', 'false', 'error'].
        Returns:
            (bool): if the dictionary is the queried one.
        """
        assert (
            missing_method in self._missing_methods
        ), f"Wrong missing method: {missing_method} / {self._missing_methods}."
        d = self
        for path, v in query.items():
            if path not in self:
                if missing_method == "ignore":
                    continue
                elif missing_method == "false":
                    return False
                elif missing_method == "error":
                    raise KeyError(f"Wrong path: {path}.")

            if isinstance(v, str) and v.startswith("!QUERY") and not eval(v[6:].strip()):
                return False
            if self[path] != v:
                return False
        return True

    ### internal manipulation ###
    def _update_flatten(self) -> None:
        flatten = {}
        paths = []

        def _flatten(pks, k, v, flatten, paths):
            ks = pks + [k]
            paths.append(self.delimiter.join(ks))
            if isinstance(v, dict):
                for nk, nv in v.items():
                    _flatten(ks, nk, nv, flatten, paths)
            else:
                flatten[paths[-1]] = v

        for k, v in self._d.items():
            _flatten([], k, v, flatten, paths)

        self._flatten_dict = flatten
        self._paths = paths

    ### getters ###
    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except Exception:
            return default

    def compare_dict(self, other):
        assert isinstance(other, ndict)
        output = {}
        for path, v in self._flatten_dict.items():
            other_v = other.get(path, None)
            if other_v != v:
                output[path] = v, other_v

        for path, v in other._flatten_dict.items():
            self_v = self.get(path, None)
            if self_v != v:
                output[path] = self_v, v

        return output

    @property
    def raw_dict(self):
        return deepcopy(self._d)

    @property
    def flatten_dict(self):
        return deepcopy(self._flatten_dict)

    @property
    def flatten_dict_split(self):
        return deepcopy(
            [ndict.from_flatten_dict({p: v}).raw_dict for p, v in self.flatten_dict.items()]
        )

    @property
    def paths(self):
        return deepcopy(self._paths)

    @property
    def size(self):
        return len(self._flatten_dict)

    ### setters & updators ###
    def update(self, d, ignore_missing_path=False):
        if isinstance(d, dict):
            d = ndict(d, delimiter=self.delimiter)._flatten_dict
        elif isinstance(d, ndict):
            d = d._flatten_dict
        else:
            raise TypeError(f"Unexpected type {type(d)}")

        for path, v in d.items():
            if path not in self.paths and ignore_missing_path:
                continue
            self[path] = v

    ### iterations ###
    def items(self):
        return self._d.items()

    def keys(self):
        return self._d.keys()

    def values(self):
        return self._d.values()

    ### magics ###
    def __bool__(self):
        return bool(len(self._d))

    def __contains__(self, path: str) -> bool:
        return path in self._paths

    def __delitem__(self, path: str) -> None:
        if path in self._paths:
            if self.delimiter not in path:
                del self._d[path]
            else:
                path = path.split(self.delimiter)
                del reduce(getitem, path[:-1], self._d)[path[-1]]
            self._update_flatten()

    def __getitem__(self, path: str) -> Any:
        if path not in self._paths:
            raise KeyError(path)
        if self.delimiter not in path:
            return self._d[path]
        path = path.split(self.delimiter)
        return reduce(getitem, path, self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __setitem__(self, path: str, value) -> None:
        if self.delimiter not in path:
            self._d[path] = value
        else:
            path = path.split(self.delimiter)
            v = self._d
            for node in path[:-1]:
                if node not in v:
                    v[node] = {}
                v = v[node]
            v[path[-1]] = value
        self._update_flatten()

    def __str__(self) -> str:
        return json.dumps(self._d, sort_keys=False, indent=2)

    def __eq__(self, other) -> bool:
        assert isinstance(other, ndict), f"Unexpected type {type(other)}"
        return self._flatten_dict == other._flatten_dict


NestedOrDict = Union[ndict, dict]
