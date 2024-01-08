from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

# representation of final resource for component, e.g. a list of Kubernetes manifests
Resource: TypeAlias = Sequence[Mapping[str, Any]]
