from collections.abc import Mapping
from typing import Any, TypeAlias

# representation of final resource for component, e.g. a list of Kubernetes manifests
Resource: TypeAlias = list[Mapping[str, Any]]
