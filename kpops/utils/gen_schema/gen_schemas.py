import os

import humps

from kpops.cli.pipeline_config import PipelineConfig
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.kafka_connect import (
    KafkaSinkConnector,
    KafkaSourceConnector,
)
from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp


class GenSchema:
    ROOT_DIR = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    models = {
        KafkaApp,
        KafkaSinkConnector,
        KafkaSourceConnector,
        KubernetesApp,
        ProducerApp,
        StreamsApp,
        PipelineConfig,
        BaseDefaultsComponent,
        PipelineComponent,
    }
    for model in models:
        file_name = humps.decamelize(str(model.__name__)) + ".json"
        file_path = os.path.join(ROOT_DIR, "schemas", file_name)
        f = open(file_path, "w")
        f.write(model.schema_json(indent=2))
        f.close


class CombineSchema:
    pass
    # Combine schemas here
