from __future__ import annotations

import logging
import re
from abc import ABC

from pydantic import BaseModel, Extra, Field
from typing_extensions import override

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfig, DescConfig

log = logging.getLogger("KubernetesApp")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppConfig(BaseModel):
    """Settings specific to Kubernetes apps."""

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow


class KubernetesApp(PipelineComponent, ABC):
    """Base class for all Kubernetes apps.

    All built-in components are Kubernetes apps, except for the Kafka connectors.

    :param namespace: Namespace in which the component shall be deployed
    :param app: Application-specific settings
    """

    namespace: str = Field(
        default=...,
        description=describe_attr("namespace", __doc__),
    )
    app: KubernetesAppConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )

    @override
    def _validate_custom(self, **kwargs) -> None:
        super()._validate_custom(**kwargs)
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
