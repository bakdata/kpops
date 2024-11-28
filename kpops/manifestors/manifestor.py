from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from kpops.config import get_config

if TYPE_CHECKING:
    from kpops.components.base_components import HelmApp
    from kpops.components.base_components.models.resource import Resource


class Manifestor(ABC):
    """Base class for generating manifests for different components."""

    def __init__(self):
        self.operation_mode = get_config().operation_mode

    @abstractmethod
    def generate_annotations(self) -> dict[str, str]:
        """Generate the annotations for the component based on the operation mode."""
        ...

    @abstractmethod
    def generate_manifest(self, helm_app: HelmApp) -> Resource:
        """Generate the Helm manifest for the component."""
        ...
