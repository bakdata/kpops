from collections.abc import Iterable, Mapping
from typing import Any, TypeAlias

# representation of final resource for component, e.g. a list of Kubernetes manifests
Resource: TypeAlias = Iterable[Mapping[str, Any]]
