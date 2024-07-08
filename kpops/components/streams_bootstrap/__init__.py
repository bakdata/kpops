from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import TYPE_CHECKING, Any

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

    :param app: streams-bootstrap app values
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

    @cached_property
    def app_values(self) -> dict[str, Any]:
        streams_bootstrap_app_values = self.model_dump(
            by_alias=True, exclude={"_cleaner", "from_", "to"}
        )
        cluster_values = self.helm.get_values(self.namespace, self.helm_release_name)
        return (
            streams_bootstrap_app_values
            if cluster_values is None
            else self.replace_image_tag_with_cluster_image_tag(
                cluster_values, streams_bootstrap_app_values
            )
        )

    @staticmethod
    def replace_image_tag_with_cluster_image_tag(
        cluster_values: dict[str, Any], streams_bootstrap_app_values: dict[str, Any]
    ) -> dict[str, Any]:
        app_values = streams_bootstrap_app_values.get("app")
        if app_values:
            app_values["imageTag"] = cluster_values["imageTag"]

        return streams_bootstrap_app_values

    @pydantic.model_validator(mode="after")
    def warning_for_latest_image_tag(self) -> Self:
        if self.validate_ and self.app.image_tag == "latest":
            log.warning(
                f"The image tag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable image tag."
            )
        return self
