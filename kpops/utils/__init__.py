from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING, Any, Concatenate, Generic, TypeVar

_T = TypeVar("_T")
_R = TypeVar("_R")

if TYPE_CHECKING:

    def cached_classproperty(
        func: Callable[Concatenate[Any, ...], _R], attrname: str | None = None
    ) -> _R: ...

else:

    class cached_classproperty(cached_property, Generic[_T, _R]):
        def __get__(self, owner_obj: _T, owner_cls: type[_T]) -> _R:
            self.func: Callable[[type[_T]], _R]
            return self.func(owner_cls)
