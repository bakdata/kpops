from typing import Any

from schema_registry.client.schema import AvroSchema

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)


class CustomSchemaProvider(SchemaProvider):
    def provide_schema(self, schema_class: str, models: dict[str, Any]) -> Schema:
        return AvroSchema({})
