from collections.abc import Iterator
from typing import Any, ClassVar, Self

import pydantic
import yaml
from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.utils.pydantic import CamelCaseConfigModel, by_alias

K8S_LABEL_MAX_LEN = 63
# https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs
K8S_CRON_JOB_NAME_MAX_LEN = 52


class ObjectMeta(CamelCaseConfigModel):
    """Metadata for all Kubernetes objects.

    https://gtsystem.github.io/lightkube-models/1.19/models/meta_v1/#objectmeta

    """

    annotations: dict[str, str] | None = None
    creation_timestamp: str | None = Field(
        default=None, description="Timestamp in RFC3339 format"
    )
    finalizers: list[str] | None = None
    labels: dict[str, str] | None = None
    name: str | None = None
    namespace: str | None = None
    resource_version: str | None = None
    uid: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @pydantic.model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        result = default_serialize_handler(self)
        return {
            by_alias(self, name): value
            for name, value in result.items()
            if name in self.model_fields_set
        }


class KubernetesManifest(CamelCaseConfigModel):
    api_version: str
    kind: str
    metadata: ObjectMeta
    _required: set[str] = pydantic.PrivateAttr({"api_version", "kind"})

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @classmethod
    def from_yaml(cls, /, content: str) -> Iterator[Self]:
        manifests: Iterator[dict[str, Any]] = yaml.safe_load_all(content)
        for manifest in manifests:
            yield cls(**manifest)

    @pydantic.model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        include = self._required | self.model_fields_set
        result = default_serialize_handler(self)
        return {
            by_alias(self, name): value
            for name, value in result.items()
            if name in include
        }

    @override
    def model_dump(self, **_: Any) -> dict[str, Any]:
        return super().model_dump(mode="json")
