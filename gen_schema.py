from pathlib import Path
from typing import Annotated, Any, Sequence

from pydantic import Field, schema, schema_json_of
from pydantic.fields import ModelField
from pydantic.schema import SkipField

import tomllib
import json

from kpops.cli.pipeline_config import PipelineConfig
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.kafka_connect import (
    KafkaSinkConnector,
    KafkaSourceConnector,
)
from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp


def write(contents: str, path: Path) -> None:
    with open(path, "w") as f:
        print(contents, file=f)


original_field_schema = schema.field_schema


# adapted from https://github.com/tiangolo/fastapi/issues/1378#issuecomment-764966955
def field_schema(field: ModelField, **kwargs: Any) -> Any:
    if field.field_info.extra.get("hidden_from_schema"):
        raise SkipField(f"{field.name} field is being hidden")
    else:
        return original_field_schema(field, **kwargs)


schema.field_schema = field_schema

PipelineComponent = (
    KubernetesApp
    | KafkaApp
    | StreamsApp
    | ProducerApp
    | KafkaSourceConnector
    | KafkaSinkConnector
)


AnnotatedPipelineComponent = Annotated[
    PipelineComponent, Field(discriminator="schema_type")
]


schema = schema_json_of(
    Sequence[AnnotatedPipelineComponent],
    title="kpops pipeline schema",
    by_alias=True,
    indent=4,
).replace("schema_type", "type")
path_schema_pipeline = Path("schema_pipeline.json")
write(schema, path_schema_pipeline)

schema = schema_json_of(PipelineConfig, title="kpops config schema", indent=4)
path_schema_config = Path("schema_config.json")
write(schema, path_schema_config)

# Generate json file for editor integration
#
# link generation for schemas, GitHub-specific
link_github_prefix = "https://raw.githubusercontent.com/"
with open("pyproject.toml", "rb") as f:
    repo = tomllib.load(f).get("tool").get("poetry").get("repository")[19:]
repo = link_github_prefix + repo + "/main/"

# files to associate with each schema
settings = dict([("yaml.schemas", {})])
settings["yaml.schemas"][repo + str(path_schema_config)] = "config.yaml"
settings["yaml.schemas"][repo + str(path_schema_pipeline)] = "pipeline.yaml"
# make settings pretty
settings = json.dumps(settings, sort_keys=True, indent=4)
# write to docs resources
write(settings, Path("docs/docs/resources/editor_integration/settings.json"))
