from __future__ import annotations

from typing import Optional, Union

from .base import NestedBase
from .functional import to_plain_dict


class snd(NestedBase):
    """Simplified Nested Dictionary."""

    def __init__(
        self, d: Optional[Union[dict, NestedBase]] = None, delimiter: Optional[str] = None
    ) -> None:
        super().__init__(d=d, delimiter=delimiter)
        self._to_plan_dict()
        self._fast_inited = False

    @classmethod
    def fast_init(
        cls, d: Optional[Union[dict, NestedBase]] = None, delimiter: Optional[str] = None
    ):
        object = super().fast_init(d=d, delimiter=delimiter)
        object._fast_inited = True
        return object

    @property
    def raw_is_plain(self) -> bool:
        return not self._fast_inited

    @property
    def dict(self) -> dict:
        return self._d

    def _to_plan_dict(self) -> None:
        self._d = to_plain_dict(self)
