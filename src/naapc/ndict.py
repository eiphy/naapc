from __future__ import annotations

import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Callable, Optional, Union

import yaml

from .dict_traverse import traverse
from .stop_conditions import generate_depth_stop_condition


def in_or_callable(d: Union[ndict, dict], k: Union[str, Callable]) -> bool:
    return isinstance(k, Callable) or isinstance(k, str) and k in d


# TODO: depth change to max_depth.
# TODO: add comments.
# TODO: Change keys, values and items to generators.
class ndict:
    """Nested dictionary.

    Users shouldn't modify the underling data outside of ndict class. Value overwritten is enabled.

    Args:
        d (Optional[Union[ndict, dict]]): If d is a dict, do make sure the path separator is the givein delimiter if 
            path is used as key.
        delimiter (str): Path separator. Can be any string.
    """

    ALL_MISSING_METHODS = ["ignore", "false", "exception"]

    def __init__(self, d: Optional[Union[ndict, dict]] = None, delimiter: str = ";") -> None:
        assert isinstance(delimiter, str), f"delimiter must be str, but recieved {type(delimiter)}"

        self._delimiter = delimiter
        self._d = {}
        self._flatten_dict = {}

        if isinstance(d, ndict):
            self.load_state_dict(d.state_dict())
        elif isinstance(d, dict):
            for k, v in d.items():
                self[k] = v
        else:
            assert d is None, f"Unexpected type {type(d)}"

    @property
    def dict(self) -> dict:
        """Underling dictionary. Do not change it!"""
        return self._d

    @property
    def flatten_dict(self) -> dict[str, Any]:
        """Flattened dictionary of {path: value} pairs."""
        return self._flatten_dict

    @property
    def paths(self) -> list[str]:
        """Get all possible paths."""
        def _path_action(tree: dict, res: list, node: Any, path: str, depth: int) -> None:
            if path is not None:
                res.append(path)

        res = []
        traverse(self.dict, res, _path_action)
        return res

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: str) -> None:
        if delimiter == self._delimiter:
            return
        self._flatten_dict = {p.replace(self._delimiter, delimiter): v for p, v in self.flatten_dict.items()}
        self._delimiter = delimiter

    def state_dict(self) -> dict:
        return {"dict": self.dict, "flatten_dict": self.flatten_dict, "delimiter": self.delimiter}

    def load_state_dict(self, states: dict) -> ndict:
        """The delimiter is only for properly initialize the object."""
        assert isinstance(states["delimiter"], str), f"Unexpected delimiter type: {states['delimiter']}."
        delimiter = self.delimiter
        self._d = states["dict"]
        self._flatten_dict = states["flatten_dict"]
        self._delimiter = states["delimiter"]
        self.delimiter = delimiter
        return self

    def get(
        self,
        path: Optional[str] = None,
        keys: Optional[list[Union[str, tuple[str, Callable]]]] = None,
        default: Optional[Any] = None,
    ) -> Union[Any, dict[str, Any]]:
        """Get values from the nested dictionary.

        Args:
            path (Optional[str] = None):
            keys (Optional[list[Union[str, tuple[str, Callable]]]] = None). Callables should accept self (ndict), 
                path: str 2 arguments.
        """
        def _get_value_or_default(key: Union[str, Callable], default: Any, path: Optional[str] = None) -> Any:
            if isinstance(key, str):
                return self[key] if key in self else default

            assert isinstance(key, Callable), f"Unexpected key type: {key}."
            try:
                return key(self, path)
            except:
                return default

        if keys is None:
            assert path is not None, "Must provide path or keys!"
            return self[path] if path in self else default

        keys = keys or []
        if path is not None:
            keys.append(path)

        return {
            **{k: _get_value_or_default(k, default) for k in keys if isinstance(k, str)},
            **{
                k[0]: _get_value_or_default(k[1], default, path=k[0])
                for k in keys
                if isinstance(k, tuple)
            },
        }

    def update(
        self, d: Union[dict, ndict], ignore_none: bool = True, ignore_missing: bool = False
    ) -> None:
        """Could be slow at current stage.

        Note that if leaves of the d is Callable, the leaves will be invoked with self: ndict and path: str 2 arguments.
        """
        d = ndict(d).flatten_dict
        for p, v in d.items():
            if v is None and ignore_none or p not in self.flatten_dict:
                continue
            self[p] = v(self, p) if isinstance(v, Callable) else v

    def keys(self, depth: int = -1) -> list[str]:
        def _keys_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            res.append(path)

        res = []
        traverse(tree=self.dict, res=res, actions=_keys_action, depth=depth)
        return res

    def values(self, depth: int = -1) -> list[Any]:
        def _values_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            res.append(node)

        res = []
        traverse(tree=self.dict, res=res, actions=_values_action, depth=depth)
        return res

    def items(self, depth: int = -1) -> list[tuple[str, Any]]:
        def _items_action(
            tree: dict, res: list[tuple[str, Any]], node: Any, path: str, depth: int
        ):
            res.append((path, node))

        res = []
        traverse(tree=self.dict, res=res, actions=_items_action, depth=depth)
        return res

    def size(self, depth: int = -1, ignore_none: bool = True) -> int:
        def _size_action(tree: dict, res: int, node: Any, path: str, depth: int):
            res += 1

        res = 0
        traverse(tree=self.dict, res=res, actions=_size_action, depth=depth)
        return res

    # TODO: Support a dummy path for aggregating in self ndict.
    def eq(
        self,
        d: Union[ndict, dict],
        keys: Optional[Union[dict, ndict]] = None,
        includes: Optional[list[str]] = None,
        excludes: Optional[list[str]] = None,
        ignore_none: bool = True,
        missing_method: str = "ignore",
    ) -> bool:
        """Determine if two nested dictionary is equavelent.

        Support customized comparison rules.

        Args:
            d: Can be both nested dictionary or flatten dictionary. Callables should accept self: ndict, d: ndict, p:
                str 3 arguments.
            keys: Used to specify the path mapping. Users may compare 1 path to another specified path. Callables should
                accept self: ndict, d: ndict, p: str 3 arguments.
            ignore_none: ignore the comparison if the value is None in self ndict. (Note that null value in d is also
                compared)
            missing_method: ignore: Won't include a path if it is missed in either party. false: Will retrun False if it
                is missed in either party. exception: raise KeyError exception if is missed in either party.
        """
        d = ndict(d)
        keys = self._get_compare_keys(
            d=d,
            keys=keys,
            includes=includes,
            excludes=excludes,
            ignore_none=ignore_none,
            missing_method=missing_method,
        )
        for ps, pt in keys.items():
            if (
                ps == False
                or pt == False
                or self._get_compare_value(self, ps) != self._get_compare_value(d, pt)
            ):
                return False
        return True

    # TODO: Support a dummy path for aggregating in self ndict.
    def diff(
        self,
        d: Union[ndict, dict],
        keys: Optional[Union[dict, ndict]] = None,
        includes: Optional[list[str]] = None,
        excludes: Optional[list[str]] = None,
        ignore_none: bool = True,
    ) -> dict[str, tuple[Any, Any]]:
        d = ndict(d)
        keys = self._get_compare_keys(
            d=d,
            keys=keys,
            includes=includes,
            excludes=excludes,
            ignore_none=ignore_none,
            missing_method="exception",
        )
        res = {}
        for ps, pt in keys.items():
            vs = self._get_compare_value(self, ps) if ps in self else None
            vt = self._get_compare_value(self, pt) if in_or_callable(d, pt) else None
            if vs != vt or (vs is None and vt is not None or vs is not None and vt is None):
                res[ps] = (vs, vt)
        return res

    def __getitem__(self, key: Union[str, int]) -> Any:
        path = key if isinstance(key, str) else list(self.keys())[key]
        return self._get_node(path, dict_as_ndict=True)

    def __delitem__(self, path: str) -> None:
        path_list = path.split(self._delimiter)
        d = self._get_node(path_list[:-1], dict_as_ndict=False)
        del d[path_list[-1]]
        if path:
            self._flatten_dict = {p: v for p, v in self._flatten_dict.items() if not p.startswith(path)}
        else:
            self._flatten_dict = {p: v for p, v in self._flatten_dict.items() if not p.startswith(";") and p != ""}
        if len(d) == 0:
            if len(path_list) > 1:
                parent_path = self._delimiter.join(path_list[:-1])
                self._flatten_dict[parent_path] = {}

    # TODO A more efficient approach.
    def __setitem__(self, path: str, value: Any) -> None:
        """Update values of the corresponding path.
        
        Args:
            path (str): Path can be an existed or non-exist path. If it's existed path and the corresponding values is 
                not a dictionary, then the original value will be overwrittern.
            value (Any): The value for that path.
        """
        assert isinstance(path, str), f"Path can only be str, recieved {type(path)}."
        path_list = path.split(self.delimiter)

        # Adjust dict.
        d = self._d
        for i, node in enumerate(path_list[:-1]):
            if node not in d:
                d[node] = {}
            elif not isinstance(d[node], dict):
                d[node] = {}
                tmp_p = self.delimiter.join(path_list[: i + 1])
                del self.flatten_dict[tmp_p]
            d = d[node]

        # Adjust flatten dict.
        if isinstance(value, Union[dict, ndict]):
            tmp = ndict(value)
            d[path_list[-1]] = tmp.dict
            for p, v in tmp.flatten_dict.items():
                combined_path = self._delimiter.join([path, p])
                self._flatten_dict[combined_path] = v
        else:
            d[path_list[-1]] = value
            self._flatten_dict[path] = value

    def __len__(self) -> int:
        return len(self.flatten_dict)

    def __bool__(self) -> bool:
        return bool(len(self) > 0)

    def __contains__(self, path: str) -> bool:
        nodes = path.split(self._delimiter)
        d = self.dict
        for n in nodes:
            if n not in d:
                return False
            d = d[n]
        return True

    def __str__(self) -> str:
        return yaml.dump(self.dict, sort_keys=False, indent=2)

    def __repr__(self) -> str:
        return f"<Nested dictionary of {len(self)} leaves.>"

    def _get_node(self, path: Union[str, list[str]], dict_as_ndict: bool) -> Any:
        """Return the value of a particular path.

        Return
            Node value. If the node is a dictionary, __class__(node) will be returned.
        """
        if isinstance(path, list):
            path_list = path
            path = self.delimiter.join(path)
        elif isinstance(path, str):
            path_list = path.split(self.delimiter)
        else:
            raise ValueError(f"Unexpected path type: {type(path)}")

        v = reduce(getitem, path_list, self._d)

        if isinstance(v, dict) and dict_as_ndict:
            flatten_dict = {p.replace(f"{path}{self.delimiter}", ""): v for p, v in self.flatten_dict.items() if p.startswith(path)}
            states = {"dict": v, "flatten_dict": flatten_dict, "delimiter": self.delimiter}
            return self.__class__(delimiter=self.delimiter).load_state_dict(states)
        else:
            return v

    def _flatten(self) -> dict[str, Any]:
        def flatten_action(tree: dict, res: dict, node: Any, path: str, depth: int) -> None:
            if not isinstance(node, dict):
                res[path] = node

        res = {}
        traverse(self.dict, res, flatten_action)
        return res

    # TODO: A more efficient way to get the compare keys.
    def _get_compare_keys(
        self,
        d: ndict,
        keys: Optional[Union[dict, ndict]],
        includes: Optional[list[str]],
        excludes: Optional[list[str]],
        ignore_none: bool,
        missing_method: str,
    ) -> dict[str, Union[str, Callable]]:
        assert (
            missing_method in self.ALL_MISSING_METHODS
        ), f"{missing_method} method is not in {self.ALL_MISSING_METHODS}."
        excludes = excludes or []
        if keys is None:
            keys = {k: k for k in self.flatten_dict.keys() if k not in excludes}
        else:
            keys = {k: v for k, v in keys.items() if k not in excludes}
        includes = [] if includes is None else [k for k in includes if k not in excludes]
        keys.update({k: k for k in includes})

        if missing_method == "ignore":
            keys = {k: v for k, v in keys.items() if k in self and in_or_callable(d, v)}
        elif missing_method == "false":
            keys = {k: v if k in self and in_or_callable(d, v) else False for k, v in keys.items()}

        if ignore_none:
            keys = {k: v for k, v in keys.items() if self[k] is not None}

        return keys

    def _get_compare_value(self, d: ndict, p: Union[str, Callable]) -> Any:
        return d.get(p, default=None) if isinstance(p, str) else p(self, d, p)
