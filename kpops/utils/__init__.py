from functools import cached_property
from typing import Generic, TypeVar

_T = TypeVar("_T")
_R = TypeVar("_R")


class cached_classproperty(cached_property, Generic[_T, _R]):
    def __get__(self, owner_obj: _T, owner_cls: type[_T]) -> _R:
        return self.func(owner_cls)
