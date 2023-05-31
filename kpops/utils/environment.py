import os
import platform
from collections import UserDict
from typing import Callable


class Environment(UserDict):
    def __init__(self, mapping=None, /, **kwargs) -> None:
        transformation = Environment.__get_transformation()
        if mapping is not None:
            mapping = {transformation(key): value for key, value in mapping.items()}
        else:
            mapping = {}
        if kwargs:
            mapping.update(
                {transformation(key): value for key, value in kwargs.items()}
            )
        super().__init__(mapping)

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


ENV = Environment(os.environ)
