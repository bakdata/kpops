from abc import ABC

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
