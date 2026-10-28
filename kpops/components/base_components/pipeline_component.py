from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterable, Iterator
from operator import itemgetter
from typing import Any, ClassVar

import pydantic
from pydantic import (
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
)

from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.components.common.topic import KafkaTopic
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.utils.pydantic import exclude_by_name, exclude_by_value

GENERATE_LEADING_KEYS = ("enabled", "prefix", "from", "to")


def leading_keys_first[T](items: Iterable[T], key: Callable[[T], str] = str) -> list[T]:
    """Keep common keys at the top, independent of the MRO-based field order.

    capability fields such as `from`/`to` are declared on mixins late in the MRO.

    :param items: Items to order
    :param key: Maps an item to its serialized key name
    :returns: The items with leading keys first, remaining order unchanged
    """
    return sorted(
        items,
        key=lambda item: (
            GENERATE_LEADING_KEYS.index(name)
            if (name := key(item)) in GENERATE_LEADING_KEYS
            else len(GENERATE_LEADING_KEYS)
        ),
    )


class PipelineComponent(BaseDefaultsComponent, ABC):
    """Base class for all components.

    :param name: Component name
    :param prefix: Pipeline prefix that will prefix every component name.
        If you wish to not have any prefix you can specify an empty string.,
        defaults to "${pipeline.name}-"
    """

    name: str
    enabled: bool = Field(
        default=True,
        title="Enabled",
        description="Whether the component is enabled and should be included in the pipeline",
    )
    prefix: str = "${pipeline.name}-"

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow", use_enum_values=False
    )

    @pydantic.model_serializer(mode="wrap", when_used="always")
    def sort_model(
        self,
        default_serialize_handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ) -> dict[str, Any]:
        result = default_serialize_handler(self)
        if info.context != "generate":
            return result
        ordered_fields = {"type": self.type, "name": self.name}
        result = exclude_by_name(result, *ordered_fields.keys())
        # NOTE: from SerializeAsOptionalModel
        if info.exclude_none:
            result = exclude_by_value(result, None)
        return {
            **ordered_fields,
            **dict(leading_keys_first(result.items(), key=itemgetter(0))),
        }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._apply_topic_sections()

    @pydantic.model_validator(mode="before")
    @classmethod
    def reject_unsupported_topic_sections(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, field_name in (
                ("from", "from_"),
                ("from_", "from_"),
                ("to", "to"),
            ):
                if data.get(key) is not None and field_name not in cls.model_fields:
                    msg = f"Component type '{cls.type}' does not support the `{key.rstrip('_')}` section."
                    raise ValueError(msg)
        return data

    def _apply_topic_sections(self) -> None:
        """Apply `from`/`to` sections to the component config."""

    @property
    def id(self) -> str:
        """Unique identifier of this component."""
        return self.name

    @property
    def full_name(self) -> str:
        return self.prefix + self.name

    @property
    def inputs(self) -> Iterator[KafkaTopic]:
        yield from ()

    @property
    def outputs(self) -> Iterator[KafkaTopic]:
        yield from ()

    def inflate(self) -> list[PipelineComponent]:
        """Inflate component.

        This is helpful if one component should result in multiple components.
        To support this, override this method and return a list of components
        the component you result in. The order of the components is the order
        the components will be deployed in.
        """
        return [self]

    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        """Render Kubernetes manifests for deploy."""
        return ()

    def manifest_destroy(self) -> tuple[KubernetesManifest, ...]:
        """Render Kubernetes manifests resources for destroy."""
        return ()

    def manifest_reset(self) -> tuple[KubernetesManifest, ...]:
        """Render Kubernetes manifests resources for reset."""
        return ()

    def manifest_clean(self) -> tuple[KubernetesManifest, ...]:
        """Render Kubernetes manifests resources for clean."""
        return ()

    def generate(self) -> dict[str, Any]:
        return self.model_dump(
            context="generate", mode="json", by_alias=True, exclude_none=True
        )

    async def deploy(self, dry_run: bool) -> None:
        """Deploy component, e.g. to Kubernetes cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    async def destroy(self, dry_run: bool) -> None:
        """Uninstall component, e.g. from Kubernetes cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    async def reset(self, dry_run: bool) -> None:
        """Reset component state.

        :param dry_run: Whether to do a dry run of the command
        """
        await self.destroy(dry_run)

    async def clean(self, dry_run: bool) -> None:
        """Destroy component including related states.

        :param dry_run: Whether to do a dry run of the command
        """
        await self.destroy(dry_run)
