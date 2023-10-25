from collections import UserDict

import yaml

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class KubernetesManifest(UserDict):
    """Specification of a Kubernetes API object."""

    @classmethod
    def from_yaml(cls, /, content: str) -> Self:
        manifest: dict = yaml.load(content, yaml.Loader)
        return cls(manifest)
