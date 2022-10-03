import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any


class NDict:
    def __init__(self, dictionary: dict) -> None:
        dictionary = deepcopy(dictionary)
        if isinstance(dictionary, NDict):
            self._d = dictionary.raw_dict
        elif isinstance(dictionary, dict):
            self._d = dictionary
        else:
            raise TypeError(f"Unexpected type {type(dictionary)}.")
        self._update_flatten()

    @classmethod
    def from_flatten_dict(cls, flatten_dict: dict) -> "NDict":
        nd = cls({})
        nd.update(flatten_dict)
        return nd

    ### internal manipulation ###
    def _update_flatten(self) -> None:
        flatten = {}
        paths = []

        def _flatten(pks, k, v, flatten, paths):
            ks = pks + [k]
            paths.append(";".join(ks))
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
        assert isinstance(other, NDict)
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
        return self._d

    @property
    def flatten_dict(self):
        return self._flatten_dict

    @property
    def paths(self):
        return self._paths

    @property
    def size(self):
        return len(self._flatten_dict)

    ### setters & updators ###
    def update(self, d, ignore_missing_path=False):
        if isinstance(d, dict):
            d = NDict(d)._flatten_dict
        elif isinstance(d, NDict):
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
            if ";" not in path:
                del self._d[path]
            else:
                path = path.split(";")
                del reduce(getitem, path[:-1], self._d)[path[-1]]
            self._update_flatten()

    def __getitem__(self, path: str) -> Any:
        if path not in self._paths:
            raise KeyError(path)
        if ";" not in path:
            return self._d[path]
        path = path.split(";")
        return reduce(getitem, path, self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __setitem__(self, path: str, value) -> None:
        if ";" not in path:
            self._d[path] = value
        else:
            path = path.split(";")
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
        assert isinstance(other, NDict), f"Unexpected type {type(other)}"
        return self._flatten_dict == other._flatten_dict
