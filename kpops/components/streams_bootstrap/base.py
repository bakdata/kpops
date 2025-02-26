from __future__ import annotations

import logging
import re
from abc import ABC
from typing import Self

import pydantic
from pydantic import Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components import KafkaApp
from kpops.components.base_components.helm_app import HelmApp
from kpops.components.streams_bootstrap.model import StreamsBootstrapValues
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.manifests.strimzi.kafka_topic import StrimziKafkaTopic
from kpops.utils.docstring import describe_attr

STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)

STREAMS_BOOTSTRAP_VERSION = "3.6.1"
STREAMS_BOOTSTRAP_VERSION_PATTERN = r"^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z]+(\.[a-zA-Z]+)?)?$"
COMPILED_VERSION_PATTERN = re.compile(STREAMS_BOOTSTRAP_VERSION_PATTERN)

log = logging.getLogger("StreamsBootstrap")


class StreamsBootstrap(KafkaApp, HelmApp, ABC):
    """Base for components with a streams-bootstrap Helm chart.

    :param values: streams-bootstrap Helm values
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "3.6.1"
    """

    values: StreamsBootstrapValues = Field(
        description=describe_attr("values", __doc__),
    )

    repo_config: HelmRepoConfig = Field(
        default=STREAMS_BOOTSTRAP_HELM_REPO,
        description=describe_attr("repo_config", __doc__),
    )

    version: str = Field(
        default=STREAMS_BOOTSTRAP_VERSION,
        pattern=STREAMS_BOOTSTRAP_VERSION_PATTERN,
        description=describe_attr("version", __doc__),
    )

    @pydantic.field_validator("version", mode="after")
    @classmethod
    def version_validator(cls, version: str) -> str:
        pattern_match = COMPILED_VERSION_PATTERN.match(version)

        if not pattern_match:
            msg = f"Invalid version format: {version}"
            raise ValueError(msg)

        major, minor, patch, suffix, _ = pattern_match.groups()
        major = int(major)

        if major != 3:
            msg = f"When using the streams-bootstrap component your version ('{version}') must be at least 3.0.1."
            raise ValueError(msg)

        return version

    @pydantic.model_validator(mode="after")
    def warning_for_latest_image_tag(self) -> Self:
        if self.validate_ and (
            not self.values.image_tag or self.values.image_tag == "latest"
        ):
            log.warning(
                f"The image tag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable image tag."
            )
        return self

    @override
    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        resource = super().manifest_deploy()
        if self.to:
            resource = resource + tuple(
                StrimziKafkaTopic.from_topic(topic) for topic in self.to.kafka_topics
            )

        return resource

    @override
    def manifest_destroy(self) -> tuple[KubernetesManifest, ...]:
        if self.to:
            return tuple(
                StrimziKafkaTopic.from_topic(topic) for topic in self.to.kafka_topics
            )
        return ()
