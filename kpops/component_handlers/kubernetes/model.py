import json
from collections import UserDict
from collections.abc import Iterator

import yaml

from kpops.utils.types import JsonType

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class KubernetesManifest(UserDict[str, JsonType]):
    """Representation of a Kubernetes API object as YAML/JSON mapping."""

    @classmethod
    def from_yaml(cls, /, content: str) -> Iterator[Self]:
        manifests: Iterator[dict[str, JsonType]] = yaml.load_all(content, yaml.Loader)
        for manifest in manifests:
            yield cls(manifest)

    @classmethod
    def from_json(cls, /, content: str) -> Self:
        manifest: dict[str, JsonType] = json.loads(content)
        return cls(manifest)
