from pydantic import BaseModel, Extra, Field

from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)
from kpops.utils.pydantic import CamelCaseConfig
from kpops.utils.yaml_loading import substitute


class KafkaStreamsConfig(BaseModel):
    brokers: str
    schema_registry_url: str | None = Field(default=None, alias="schemaRegistryUrl")

    class Config(CamelCaseConfig):
        extra = Extra.allow


class KafkaAppConfig(KubernetesAppConfig):
    streams: KafkaStreamsConfig
    nameOverride: str | None


class KafkaApp(KubernetesApp):
    """
    Base component for kafka-based components.
    Producer or streaming apps should inherit from this class.
    """

    _type = "kafka-app"
    app: KafkaAppConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.streams.brokers = substitute(
            self.app.streams.brokers, {"broker": self.config.broker}
        )
        if self.app.streams.schema_registry_url:
            self.app.streams.schema_registry_url = substitute(
                self.app.streams.schema_registry_url,
                {"schema_registry_url": self.config.schema_registry_url},
            )

    def to_helm_values(self):
        return self.app.dict(by_alias=True, exclude_none=True, exclude_unset=True)

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release. Can be overridden."""
        return self.name
