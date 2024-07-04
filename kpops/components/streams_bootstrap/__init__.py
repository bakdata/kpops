import logging
from abc import ABC
from typing import Any, Self

import pydantic
from pydantic import Field

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.component_handlers.kubernetes.utils import validate_image_tag
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.utils.docstring import describe_attr

STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)
STREAMS_BOOTSTRAP_VERSION = "2.9.0"

log = logging.getLogger("StreamsBootstrap")


class StreamsBootstrapValues(HelmAppValues):
    """Base value class for all streams bootstrap related components.

    :param image_tag: Docker image tag of the Kafka Streams app.
    """

    image_tag: str = Field(
        default="latest", description=describe_attr("image_tag", __doc__)
    )

    @pydantic.field_validator("image_tag", mode="before")
    @classmethod
    def validate_image_tag_field(cls, image_tag: Any) -> str:
        return validate_image_tag(image_tag)


class StreamsBootstrap(HelmApp, ABC):
    """Base for components with a streams-bootstrap Helm chart.

    :param app: Streams bootstrap app values
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "2.9.0"
    """

    app: StreamsBootstrapValues = Field(
        default_factory=StreamsBootstrapValues,
        description=describe_attr("app", __doc__),
    )

    repo_config: HelmRepoConfig = Field(
        default=STREAMS_BOOTSTRAP_HELM_REPO,
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default=STREAMS_BOOTSTRAP_VERSION,
        description=describe_attr("version", __doc__),
    )

    @pydantic.model_validator(mode="after")
    def warning_for_latest_image_tag(self) -> Self:
        if self.validate_ and self.app.image_tag == "latest":
            log.warning(
                f"The imageTag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable imageTag."
            )
        return self
