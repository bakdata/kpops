from abc import ABC
from functools import cached_property
from typing import Any

from pydantic import Field

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components.helm_app import HelmApp
from kpops.utils.docstring import describe_attr

STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)
STREAMS_BOOTSTRAP_VERSION = "2.9.0"


class StreamsBootstrap(HelmApp, ABC):
    """Base for components with a streams-bootstrap Helm chart.

    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "2.9.0"
    """

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
        cluster_values = self.helm_values()
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
