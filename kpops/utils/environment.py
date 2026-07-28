import os
from collections import UserDict
from collections.abc import ItemsView, KeysView, Mapping, MutableMapping, ValuesView

from typing_extensions import override

PIPELINE_PATH = "pipeline.path"


class Environment(UserDict[str, str]):
    """Internal environment wrapping OS environment."""

    def __init__(
        self, mapping: MutableMapping[str, str] | None = None, /, **kwargs: str
    ) -> None:
        self._global: Mapping[str, str] = os.environ
        if mapping is None:
            mapping = {}
        if kwargs:
            mapping.update(**kwargs)
        super().__init__(mapping)

    @override
    def __getitem__(self, key: str) -> str:
        try:
            return self.data[key]
        except KeyError:
            return self._global[key]

    @override
    def __contains__(self, key: object) -> bool:
        return super().__contains__(key) or self._global.__contains__(key)

    @property
    def _dict(self) -> dict[str, str]:
        return {**self._global, **self.data}

    @override
    def keys(self) -> KeysView[str]:
        return KeysView(self._dict)

    @override
    def values(self) -> ValuesView[str]:
        return ValuesView(self._dict)

    @override
    def items(self) -> ItemsView[str, str]:
        return ItemsView(self._dict)


ENV = Environment()
