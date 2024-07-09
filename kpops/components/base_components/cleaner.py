from abc import ABC

from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmFlags
from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_name_override,
    create_helm_release_name,
)
from kpops.components.base_components.helm_app import HelmApp
from kpops.config import get_config


class Cleaner(HelmApp, ABC):
    """Generic Helm app for cleaning or resetting."""

    suffix: str = "-clean"

    @property
    @override
    def full_name(self) -> str:
        return super().full_name + self.suffix

    @property
    @override
    def helm_release_name(self) -> str:
        return create_helm_release_name(self.full_name, self.suffix)

    @property
    @override
    def helm_name_override(self) -> str:
        return create_helm_name_override(self.full_name, self.suffix)

    @property
    @override
    def helm_flags(self) -> HelmFlags:
        return HelmFlags(
            create_namespace=get_config().create_namespace,
            version=self.version,
            wait=True,
            wait_for_jobs=True,
        )
