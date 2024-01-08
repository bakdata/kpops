from __future__ import annotations

from abc import ABC

from pydantic import AliasChoices, ConfigDict, Field

from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.components.base_components.models.from_section import (
    FromSection,
)
from kpops.components.base_components.models.resource import Resource
from kpops.utils.docstring import describe_attr


class PipelineComponent(BaseDefaultsComponent, ABC):
    """Base class for all components.

    :param name: Component name
    :param prefix: Pipeline prefix that will prefix every component name.
        If you wish to not have any prefix you can specify an empty string.,
        defaults to "${pipeline_name}-"
    :param from_: Topic(s) and/or components from which the component will read
        input, defaults to None
    """

    name: str = Field(default=..., description=describe_attr("name", __doc__))
    prefix: str = Field(
        default="${pipeline_name}-",
        description=describe_attr("prefix", __doc__),
    )
    from_: FromSection | None = Field(
        default=None,
        serialization_alias="from",
        validation_alias=AliasChoices("from", "from_"),
        title="From",
        description=describe_attr("from_", __doc__),
    )
    to: None = None

    model_config = ConfigDict(
        extra="allow",
    )

    @property
    def full_name(self) -> str:
        return self.prefix + self.name

    def inflate(self) -> list[PipelineComponent]:
        """Inflate component.

        This is helpful if one component should result in multiple components.
        To support this, override this method and return a list of components
        the component you result in. The order of the components is the order
        the components will be deployed in.
        """
        return [self]

    def manifest(self) -> Resource:
        """Render final component resources, e.g. Kubernetes manifests."""
        return []

    def deploy(self, dry_run: bool) -> None:
        """Deploy component, e.g. to Kubernetes cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    def destroy(self, dry_run: bool) -> None:
        """Uninstall component, e.g. from Kubernetes cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    def reset(self, dry_run: bool) -> None:
        """Reset component state.

        :param dry_run: Whether to do a dry run of the command
        """

    def clean(self, dry_run: bool) -> None:
        """Destroy component including related states.

        :param dry_run: Whether to do a dry run of the command
        """
