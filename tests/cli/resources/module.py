from typing import Any

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)


class CustomSchemaProvider(SchemaProvider):
    def provide_schema(self, schema_class: str, models: dict[str, Any]) -> Schema:
        pass
