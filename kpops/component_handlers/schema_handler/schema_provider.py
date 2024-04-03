from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeAlias

from schema_registry.client.schema import AvroSchema, JsonSchema

if TYPE_CHECKING:
    from kpops.components.base_components.models import ModelName, ModelVersion

Schema: TypeAlias = AvroSchema | JsonSchema


class SchemaProvider(ABC):
    @abstractmethod
    def provide_schema(
        self, schema_class: str, models: dict[ModelName, ModelVersion]
    ) -> Schema: ...
