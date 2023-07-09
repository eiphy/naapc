from __future__ import annotations
import yaml

import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union, Callable
from .stop_conditions import generate_depth_stop_condition
from .dict_traverse import traverse


# TODO: depth change to max_depth.
# TODO: invoking internal implemntations using kwargs.
class ndict:
    """Due to the internal mechanism, modifications of the raw_dict will not be applied on the
    object."""

    _ALL_MISSING_METHODS = ["ignore", "false", "exception"]

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
            self.update(d)
        else:
            raise TypeError(f"Unexpected type {type(d)}.")

    @property
    def dict(self) -> dict:
        return self._d

    @property
    def flatten_dict(self) -> dict[str, Any]:
        return self._flatten_dict

    @property
    def paths(self) -> list[str]:
        def _path_action(tree: dict, res: list, node: Any, path: str, depth: int) -> None:
            res.append(path)

        res = []
        traverse(self.dict, res, _path_action)
        return res

    def get(
        self,
        path: Optional[str] = None,
        keys: Optional[list[Union[str, tuple[str, Callable]]]] = None,
        default: Optional[Any] = None,
    ) -> Union[Any, dict[str, Any]]:
        """Get values from the nested dictionary.

        Args:
            keys. Callables should accept tree: ndict, path: str 2 arguments.
        """
        if keys is None:
            assert path is not None, "Must provide path or keys!"
            return self[path] if path in self else default

        keys = keys or []
        if path is not None:
            keys.append(path)

        return {
            **{k: self._get_value_or_default(k, default) for k in keys if isinstance(k, str)},
            **{
                k[0]: self._get_value_or_default(k[1], default, path=k[0])
                for k in keys
                if isinstance(k, tuple)
            },
        }

    # TODO: A more efficient implementation.
    def update(
        self, d: Union[dict, ndict], ignore_none: bool = True, ignore_missing: bool = False
    ) -> None:
        """Could be slow at current stage.

        Note that if leaves of the d is Callable, the leaves will be invoked with self: ndict and path: str 2 arguments.
        """
        d = ndict(d).flatten_dict
        if ignore_none:
            d = {p: v for p, v in d.items() if v is None}
        if ignore_missing:
            d = {p: v for p, v in d.items() if p not in self.flatten_dict}
        for p, v in d.items():
            self[p] = v(self, p) if isinstance(v, Callable) else v

    # TODO: Generator for keys.
    def keys(self, depth: int = -1) -> list[str]:
        def _keys_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            res.append(path)

        res = []
        traverse(tree=self.dict, res=res, actions=_keys_action, depth=depth)
        return res

    # TODO: Generator for values.
    def values(self, depth: int = -1) -> list[Any]:
        def _values_action(tree: dict, res: list[str], node: Any, path: str, depth: int):
            res.append(node)

        res = []
        traverse(tree=self.dict, res=res, actions=_values_action, depth=depth)
        return res

    # TODO: Generator for items.
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
        keys = self._get_compare_keys(
            d=d,
            keys=keys,
            includes=includes,
            excludes=excludes,
            ignore_none=ignore_none,
            missing_method=missing_method,
        )
        d = ndict(d)
        for ps, pt in keys.items():
            if self._get_compare_value(self, ps) != self._get_compare_value(d, pt):
                return False
        return True

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
        nodes = path.split(self._delimiter)
        d = self.dict
        for n in nodes:
            if n not in d:
                return False
            d = d[n]
        return True

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
        def flatten_action(tree: dict, res: dict, node: Any, path: str, depth: int) -> None:
            if not isinstance(node, dict):
                res[path] = node

        res = {}
        traverse(self.dict, res, flatten_action)
        return res

    # TODO: Maybe only catch KeyError exception.
    def _get_value_or_default(self, key: Union[str, Callable], default: Any, **kwargs) -> Any:
        if isinstance(key, str):
            return self[key] if key in self else default
        assert isinstance(key, Callable), f"Unexpected key type: {key}."

        try:
            return key(self, **kwargs)
        except:
            return default

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
            missing_method in self._ALL_MISSING_METHODS
        ), f"{missing_method} method is not in {self._ALL_MISSING_METHODS}."
        excludes = excludes or []
        if keys is None:
            keys = {k: k for k in self.flatten_dict.keys() if k not in excludes}
        else:
            keys = {k: v for k, v in keys.items() if k not in excludes}
        includes = [] if includes is None else [k for k in includes if k not in excludes]
        keys.update({k: k for k in includes})

        if missing_method == "ignore":
            keys = {k: v for k, v in keys.items() if k in self and k in d}
        elif missing_method == "false":
            keys = {k: v if k in self and k in d else False for k, v in keys.items()}

        if ignore_none:
            keys = {k: v for k, v in keys.items() if self[k] is not None}

        return keys

    def _get_compare_value(self, d: ndict, p: Union[str, Callable]) -> Any:
        return d.get(p, default=None) if isinstance(p, str) else p(self, d, p)
