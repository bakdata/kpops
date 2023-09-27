from schema_registry.client.schema import AvroSchema

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)
from kpops.components.base_components.models import ModelName, ModelVersion


class CustomSchemaProvider(SchemaProvider):
    def provide_schema(
        self, schema_class: str, models: dict[ModelName, ModelVersion]
    ) -> Schema:
        return AvroSchema()
