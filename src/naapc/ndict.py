from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Callable, Optional, Union

import yaml

from .base import NestedBase
from .dict_traverse import traverse
from .stop_conditions import generate_depth_stop_condition


def in_or_callable(d: Union[ndict, dict], k: Union[str, Callable]) -> bool:
    return isinstance(k, Callable) or isinstance(k, str) and k in d


# TODO: depth change to max_depth.
# TODO: add comments.
# TODO: Change keys, values and items to generators.
class ndict(NestedBase):
    """Nested dictionary.

    Users shouldn't modify the underling data outside of ndict class. Value overwritten is enabled.

    Args:
        d (Optional[Union[ndict, dict]]): If d is a dict, do make sure the path separator is the givein delimiter if
            path is used as key.
        delimiter (str): Path separator. Can be any string.
    """

    ALL_MISSING_METHODS = ["ignore", "false", "exception"]

    def __init__(
        self,
        d: Optional[Union[dict, NestedBase]] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ) -> None:
        self._flatten_dict = {}
        super().__init__(d=d, delimiter=delimiter, return_nested=return_nested)

    @classmethod
    def from_states(
        cls,
        states: Optional[dict] = None,
        d: Optional[dict] = None,
        flatten_dict: Optional[dict] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ) -> NestedBase:
        if states is None:
            assert d and delimiter
            assert isinstance(d, dict), f"Wrong type: {type(d)}."
            states = (
                {"dict": d, "delimiter": delimiter, "flatten_dict": flatten_dict}
                if flatten_dict is not None
                else {"dict": d, "delimiter": delimiter}
            )
        return cls(return_nested=return_nested).load_states(states)

    @property
    def raw_is_plain(self) -> bool:
        return True

    @property
    def flatten_dict(self) -> dict[str, Any]:
        """Flattened dictionary of {path: value} pairs."""
        return self._flatten_dict

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, delimiter: str) -> None:
        if delimiter == self._delimiter:
            return
        self._flatten_dict = {
            p.replace(self._delimiter, delimiter): v for p, v in self.flatten_dict.items()
        }
        self._delimiter = delimiter

    def states(self) -> dict:
        return {"dict": self.dict, "flatten_dict": self.flatten_dict, "delimiter": self.delimiter}

    def load_states(self, states: Union[dict, ndict]) -> NestedBase:
        """The delimiter is only for properly initialize the object."""
        if "flatten_dict" in states:
            self._flatten_dict = states["flatten_dict"]
            delimiter = self.delimiter
            self._d = states["dict"]
            self._delimiter = states["delimiter"]
            self.delimiter = delimiter
        else:
            tmp = self.__class__(
                d=states["dict"], delimiter=self.delimiter, return_nested=self.return_nested
            )
            self._d = tmp.dict
            self._flatten_dict = tmp.flatten_dict
        return self

    def __delitem__(self, path: str) -> None:
        path_list = path.split(self._delimiter)
        d = self._get_node(path_list[:-1])
        del d[path_list[-1]]
        if path:
            self._flatten_dict = {
                p: v for p, v in self._flatten_dict.items() if not p.startswith(path)
            }
        else:
            self._flatten_dict = {
                p: v for p, v in self._flatten_dict.items() if not p.startswith(";") and p != ""
            }
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
        path_list = path.split(self._delimiter)

        # Adjust dict.
        d = self._d
        for i, node in enumerate(path_list[:-1]):
            if node not in d:
                d[node] = {}
            elif not isinstance(d[node], dict):
                d[node] = {}
                tmp_p = self._delimiter.join(path_list[: i + 1])
                del self._flatten_dict[tmp_p]
            d = d[node]

        to_be_delete_node = [
            f"{path}{self.delimiter}{k}" for k in self._get_flatten_dict_of_subtree(path).keys()
        ]
        for k in to_be_delete_node:
            del self._flatten_dict[k]
        parent_path = self.delimiter.join(path_list[:-1])
        if parent_path in self._flatten_dict:
            assert (
                isinstance(self._flatten_dict[parent_path], dict)
                and not self._flatten_dict[parent_path]
            )
            del self._flatten_dict[parent_path]

        # Adjust flatten dict.
        if isinstance(value, Union[dict, ndict]):
            tmp = ndict(value)
            d[path_list[-1]] = tmp.dict
            if tmp.flatten_dict:
                if path in self._flatten_dict:
                    del self._flatten_dict[path]
                for p, v in tmp.flatten_dict.items():
                    combined_path = self._delimiter.join([path, p])
                    self._flatten_dict[combined_path] = v
            else:
                self._flatten_dict[path] = {}
        else:
            d[path_list[-1]] = value
            self._flatten_dict[path] = value

    def __contains__(self, path: str) -> bool:
        if path in self.flatten_dict:
            return True
        return super().__contains__(path)

    def _get_flatten_dict_of_subtree(self, prefix: str) -> dict[str, Any]:
        prefix = f"{prefix}{self.delimiter}"
        return deepcopy(
            {
                path[len(prefix) :]: value
                for path, value in self.flatten_dict.items()
                if path.startswith(prefix) and len(path) >= len(prefix)
            }
        )

    def _dict_nested_conversion_before_return(self, path: str, val: Any) -> Any:
        if self.return_nested and isinstance(val, dict):
            return self.from_states(
                {
                    "dict": val,
                    "flatten_dict": self._get_flatten_dict_of_subtree(path),
                    "delimiter": self.delimiter,
                },
                return_nested=self.return_nested,
            )
        else:
            return val
