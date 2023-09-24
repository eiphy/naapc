from typing import Union

from .base import NestedBase


def to_plain_dict(d: Union[dict, NestedBase]) -> dict:
    def _imp(node):
        if isinstance(node, dict):
            return {k: _imp(v) for k, v in node.items()}
        elif isinstance(node, NestedBase):
            return node.dict if node.raw_is_plain else {k: _imp(v) for k, v in node.dict.items()}
        elif isinstance(node, list):
            return [_imp(v) for v in node]
        elif isinstance(node, tuple):
            return _imp(list(node))
        else:
            return node

    d = d if isinstance(d, dict) else d.dict
    return {k: _imp(v) for k, v in d.items()}
