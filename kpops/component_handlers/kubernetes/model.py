import json
from collections import UserDict
from collections.abc import Iterator
from typing import TypeAlias, TypeVar

import yaml

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


# JSON values
JsonPrimitive: TypeAlias = (
    dict[str, "Json"] | list["Json"] | str | int | float | bool | None
)
Json = TypeVar("Json", bound=JsonPrimitive)


class KubernetesManifest(UserDict[str, Json]):
    """Representation of a Kubernetes API object as YAML/JSON mapping."""

    @classmethod
    def from_yaml(cls, /, content: str) -> Iterator[Self]:
        manifests: Iterator[dict[str, Json]] = yaml.load_all(content, yaml.Loader)
        for manifest in manifests:
            yield cls(manifest)

    @classmethod
    def from_json(cls, /, content: str) -> Self:
        manifest: dict[str, Json] = json.loads(content)
        return cls(manifest)
