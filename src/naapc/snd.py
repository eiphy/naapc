from __future__ import annotations

from typing import Optional, Union

from .base import NestedBase


class snd(NestedBase):
    """Simplified Nested Dictionary."""

    def __init__(
        self,
        d: Optional[Union[dict, NestedBase]] = None,
        delimiter: Optional[str] = None,
        return_nested: bool = True,
    ) -> None:
        super().__init__(d=d, delimiter=delimiter, return_nested=return_nested)

    @property
    def raw_is_plain(self) -> bool:
        return True

    @property
    def dict(self) -> dict:
        return self._d
