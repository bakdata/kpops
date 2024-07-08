from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING

import pydantic
from pydantic import Field

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.utils.docstring import describe_attr

if TYPE_CHECKING:
    try:
        from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
    except ImportError:
        from typing_extensions import Self

STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)
STREAMS_BOOTSTRAP_VERSION = "2.9.0"

log = logging.getLogger("StreamsBootstrap")

# Source of the pattern: https://kubernetes.io/docs/concepts/containers/images/#image-names
IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"


class StreamsBootstrapValues(HelmAppValues):
    """Base value class for all streams bootstrap related components.

    :param image_tag: Docker image tag of the streams-bootstrap app.
    """

    image_tag: str = Field(
        default="latest",
        pattern=IMAGE_TAG_PATTERN,
        description=describe_attr("image_tag", __doc__),
    )


class StreamsBootstrap(HelmApp, ABC):
    """Base for components with a streams-bootstrap Helm chart.

    :param values: streams-bootstrap Helm values
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "2.9.0"
    """

    values: StreamsBootstrapValues = Field(
        default_factory=StreamsBootstrapValues,
        description=describe_attr("values", __doc__),
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
        if self.validate_ and self.values.image_tag == "latest":
            log.warning(
                f"The image tag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable image tag."
            )
        return self
