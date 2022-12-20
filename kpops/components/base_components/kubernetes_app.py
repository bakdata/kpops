import logging
import re

from pydantic import BaseModel

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.pydantic import CamelCaseConfig

log = logging.getLogger("KubernetesAppComponent")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppConfig(BaseModel):
    namespace: str

    class Config(CamelCaseConfig):
        pass


# TODO: label and annotations


class KubernetesApp(PipelineComponent):
    """Base kubernetes app"""

    _type = "kubernetes-app"
    app: KubernetesAppConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_compatible_name()

    def check_compatible_name(self) -> None:
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(self.name)):  # TODO: SMARTER
            raise ValueError(
                f"The component name {self.name} is invalid for Kubernetes."
            )
