import json
from collections import UserDict
from typing import TypeAlias

import yaml

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

Json: TypeAlias = dict[str, "Json"] | list["Json"] | str | int | float | bool | None


class KubernetesManifest(UserDict[str, Json]):
    """Representation of a Kubernetes API object as YAML/JSON mapping."""

    @classmethod
    def from_yaml(cls, /, content: str) -> Self:
        manifest: dict = yaml.load(content, yaml.Loader)
        return cls(manifest)

    @classmethod
    def from_json(cls, /, content: str) -> Self:
        manifest: dict = json.loads(content)
        return cls(manifest)
