from __future__ import annotations

import json
from copy import deepcopy
from functools import reduce
from operator import getitem
from typing import Any, Optional, Union


def dfs(
    res: Any, node: Any, path: str, depth: int, action: callable, stop_condition: callable
) -> Any:
    """Depth-first traverse.

    Args:
        res (Any): Current results.
        node (Any): Current node (value).
        path (str): Current path (key)
        depth (int): Current depth (0 at root)
        action (callable): Action.
        stop_condition (callable): Whether should stop the traverse process.

    Returns:
        Any: Results
    """
    if stop_condition(res, node, path, depth):
        return res

    action(res, node, path, depth)

    if isinstance(node, dict):
        for k, v in node.items():
            next_path = ";".join([path, k])
            dfs(res, v, next_path, depth + 1, action, stop_condition)
    else:
        return res


class ndict:
    """Due to the internal mechanism, modifications of the raw_dict will not be applied on the
    object."""

    _missing_methods = ["ignore", "false", "error"]

    def __init__(self, d: Optional[Union[ndict, dict]] = None, delimiter: str = ";") -> None:
        assert isinstance(delimiter, str), f"delimiter must be str, but recieved {type(delimiter)}"
        self._delimiter = delimiter

        d = d or {}
        if isinstance(d, ndict):
            self._d = d.dict
            self._flatten_dict = d.flatten_dict
        elif isinstance(d, dict):
            self._d = d
            self._flatten_dict = self.flatten(self.dict)
        else:
            raise TypeError(f"Unexpected type {type(d)}.")

    @staticmethod
    def flatten(d: dict) -> dict[str, Any]:
        ...

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

    @property
    def dict(self) -> dict:
        return self._d

    @property
    def flatten_dict(self) -> dict:
        return self._flatten_dict

    def traverse(
        self,
        res: Any,
        actions: Union[callable, tuple[callable, dict[str, callable]]],
        depth: Optional[int] = -1,
        stop_condition: Optional[Union[list[callable], callable]] = None,
        alg: callable = dfs,
    ) -> Any:
        """Go through nodes in the tree and apply actions / collect data.

        Args:
            res (Any): Where the final results will be.
            actions (Union[callable, tuple[callable, dict[str, callable]]]): action applied on all nodes or A tuple of
                (default action, {path: path actions}). Each callable should accept: res, node, path, depth 4 arguments.
            depth (Optional[int], optional): Maximum traverse depth. Defaults to -1, which means traverse all depth.
            stop_condition (Optional[Union[list[callable], callable]], optional): Callable which returns bool to
                determine whether the tranverse should be stopped. This callable should accept res, node, path, depth 4
                arguments. It can also be a list of callables. In that case all the callable must return True to stop
                the traverse process. Defaults to None which means no extra conditions other depth.
            alg (callable, optional): Algorithm used to traverse the tree. Currently only support dfs. It should accept
                res, node, path, depth, actions and stop_condition 6 arguments. Defaults to dfs.

        Returns:
            Any: The results
        """
        action = self._generate_action_pipeline(actions)
        stop_condition = self._generate_stop_condition_pipeline(stop_condition, depth)

        return alg(res, self.dict, "", 0, action, stop_condition)

    def is_matched(self, query: dict, missing_method: str = "ignore", **kwargs) -> bool:
        """Test if the dictionary is the queried one.

        Syntax:
            1. Normal path-value pair: {path: value}.
            2. Query expression: {path: !QUERY [python expression returns boolean results]}. The
                expression can use d: the dictionary, path: the query path and kwargs.

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
        except KeyError:
            return default
        except Exception as e:
            raise e

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
    def update(self, d, ignore_missing_path=False, ignore_none=False):
        if isinstance(d, dict):
            d = ndict(d, delimiter=self.delimiter)._flatten_dict
        elif isinstance(d, ndict):
            d = d._flatten_dict
        else:
            raise TypeError(f"Unexpected type {type(d)}")

        for path, v in d.items():
            try:
                if ignore_none and v is None:
                    continue
                self[path] = v
            except KeyError as e:
                if ignore_missing_path:
                    continue
                raise e
            except Exception as e:
                raise e

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
            v = self._d[path]
        path = path.split(self.delimiter)
        v = reduce(getitem, path, self._d)
        return v

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

    def __eq__(self, other: NestedOrDict) -> bool:
        assert isinstance(other, (ndict, dict)), f"Unexpected type {type(other)}"
        return self._flatten_dict == ndict(other, self.delimiter)._flatten_dict

    def _generate_depth_stop_condition(self, max_depth: int = -1) -> callable:
        def depth_stop_condition(res: Any, node: Any, path: str, depth) -> bool:
            return max_depth != -1 and depth > max_depth

        return depth_stop_condition

    def _generate_stop_condition_pipeline(
        self, conditions: Optional[Union[list[callable], callable]], max_depth: int = -1
    ) -> callable:
        conditions = [conditions] if isinstance(conditions, callable) else conditions
        conditions = [] if conditions is None else conditions
        conditions.append(self._generate_depth_stop_condition(max_depth))

        def stop_condition_pipeline(res: Any, node: Any, path: str, depth: int) -> bool:
            for cond in conditions:
                if cond(res, node, path, depth):
                    return True
            return False

        return stop_condition_pipeline

    def _generate_action_pipeline(
        self, actions: Union[callable, tuple[callable, dict[str, callable]]]
    ) -> callable:
        if isinstance(actions, tuple):
            default_action = actions[0]
            if len(actions) == 2:
                specific_actions = actions[1]
        else:
            default_action = actions
            specific_actions = {}

        def action_pipeline(res: Any, node: Any, path: str, depth: int) -> None:
            if path in specific_actions:
                specific_actions[path](res, node, path, depth)
            else:
                default_action(res, node, path, depth)

        return action_pipeline


NestedOrDict = Union[ndict, dict]
