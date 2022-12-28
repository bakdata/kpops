from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeAlias

from schema_registry.client.schema import AvroSchema, JsonSchema

Schema: TypeAlias = AvroSchema | JsonSchema


class SchemaProvider(ABC):
    @abstractmethod
    def provide_schema(self, schema_class: str, models: dict[str, Any]) -> Schema:
        ...
