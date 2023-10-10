import os
from collections import UserDict
from collections.abc import Mapping


class Environment(UserDict[str, str]):
    def __init__(self, mapping: Mapping[str, str] | None = None, /, **kwargs) -> None:
        env = os.environ
        if mapping is not None:
            env.update(mapping)
        if kwargs:
            env.update(**kwargs)
        super().__init__(env)

    def __getitem__(self, key: str) -> str:
        if key in self.data:
            return self.data[key]
        return os.environ[key]


ENV = Environment()
