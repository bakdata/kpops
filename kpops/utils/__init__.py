from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING, Any, Concatenate

if TYPE_CHECKING:

    def cached_classproperty[R](
        func: Callable[Concatenate[Any, ...], R], attrname: str | None = None
    ) -> R: ...

else:

    class cached_classproperty[T, R](cached_property):
        def __get__(self, owner_obj: T, owner_cls: type[T]) -> R:
            self.func: Callable[[type[T]], R]
            return self.func(owner_cls)
