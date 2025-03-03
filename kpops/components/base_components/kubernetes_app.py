from __future__ import annotations

import logging
import re
from abc import ABC
from typing import ClassVar

from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfigModel, DescConfigModel

log = logging.getLogger("KubernetesApp")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppValues(CamelCaseConfigModel, DescConfigModel):
    """Settings specific to Kubernetes apps."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class KubernetesApp(PipelineComponent, ABC):
    """Base class for all Kubernetes apps.

    All built-in components are Kubernetes apps, except for the Kafka connectors.

    :param namespace: Kubernetes namespace in which the component shall be deployed
    :param values: Kubernetes app values
    """

    namespace: str = Field(
        description=describe_attr("namespace", __doc__),
    )
    values: KubernetesAppValues = Field(
        description=describe_attr("values", __doc__),
    )

    @override
    def _validate_custom(self) -> None:
        super()._validate_custom()
        self.validate_kubernetes_name(self.name)

    @staticmethod
    def validate_kubernetes_name(name: str) -> None:
        """Check if a name is valid for a Kubernetes resource.

        :param name: Name that is to be used for the resource
        :raises ValueError: The component name {name} is invalid for Kubernetes.
        """
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(name)):
            msg = f"The component name {name} is invalid for Kubernetes."
            raise ValueError(msg)
