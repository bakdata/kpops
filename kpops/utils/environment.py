import os
from collections import UserDict
from collections.abc import MutableMapping


class Environment(UserDict[str, str]):
    def __init__(
        self, mapping: MutableMapping[str, str] | None = None, /, **kwargs
    ) -> None:
        if mapping is None:
            mapping = {}
        if kwargs:
            mapping.update(**kwargs)
        super().__init__(mapping)

    def __getitem__(self, key: str) -> str:
        if key in self.data:
            return self.data[key]
        return os.environ[key]

    def __contains__(self, key: object) -> bool:
        return super().__contains__(key) or os.environ.__contains__(key)

    def keys(self) -> set[str]:
        return set(super().keys()).union(os.environ.keys())

    def values(self) -> set[str]:
        return set(super().values()).union(os.environ.values())

    def items(self) -> dict[str, str]:
        return {**os.environ, **self.data}


ENV = Environment()
