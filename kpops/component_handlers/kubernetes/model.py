from __future__ import annotations

import json
from collections import UserDict
from collections.abc import Iterator

import yaml

from kpops.utils.types import JsonType

K8S_LABEL_MAX_LEN = 63


class KubernetesManifest(UserDict[str, JsonType]):
    """Representation of a Kubernetes API object as YAML/JSON mapping."""

    @classmethod
    def from_yaml(
        cls, /, content: str
    ) -> Iterator[KubernetesManifest]:  # TODO: typing.Self for Python 3.11+
        manifests: Iterator[dict[str, JsonType]] = yaml.load_all(content, yaml.Loader)
        for manifest in manifests:
            yield cls(manifest)

    @classmethod
    def from_json(
        cls, /, content: str
    ) -> KubernetesManifest:  # TODO: typing.Self for Python 3.11+
        manifest: dict[str, JsonType] = json.loads(content)
        return cls(manifest)
