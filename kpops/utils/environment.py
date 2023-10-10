import os
import platform
from collections import UserDict
from collections.abc import Callable, Mapping


class Environment(UserDict[str, str]):
    def __init__(self, mapping: Mapping[str, str] | None = None, /, **kwargs) -> None:
        _transformer: Callable[[str], str] = Environment.__get_transformation()
        env = os.environ
        if mapping is not None:
            env.update(mapping)
        if kwargs:
            env.update(**kwargs)
        env = {_transformer(key): value for key, value in env.items()}
        super().__init__(env)

    @staticmethod
    def __key_camel_case_transform(key: str) -> str:
        return key.lower()

    @staticmethod
    def __key_identity_transform(key: str) -> str:
        return key

    @staticmethod
    def __get_transformation() -> Callable[[str], str]:
        if platform.system() == "Windows":
            return Environment.__key_camel_case_transform
        else:
            return Environment.__key_identity_transform

    def __getitem__(self, key: str) -> str:
        if key in self.data:
            return self.data[key]
        return os.environ[key]


ENV = Environment()
