import os
import platform
from typing import Callable


class Environment(dict):
    def __init__(self, mapping=None, /, **kwargs) -> None:

        transformation = self._get_transformation()
        if mapping is not None:
            mapping = {transformation(key): value for key, value in mapping.items()}
        else:
            mapping = {}
        if kwargs:
            mapping.update(
                {transformation(key): value for key, value in kwargs.items()}
            )
        super().__init__(mapping)

    def _key_camel_case_transform(self, key):
        return str(key).lower()

    def _key_identity_transform(self, key):
        return str(key)

    def _get_transformation(self) -> Callable[[str], str]:
        if platform.system() == "Windows":
            return self._key_camel_case_transform
        else:
            return self._key_identity_transform


environ = Environment(os.environ)
