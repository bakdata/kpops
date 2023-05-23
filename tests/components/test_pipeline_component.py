from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kpops.cli import pipeline_config
from kpops.cli.pipeline_config import TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.environment import environ

DEFAULTS_PATH = Path(__file__).parent / "resources"


class PlainPipelineComponent(PipelineComponent):
    type: str = "plain-pipeline-component"


@pytest.fixture
def prefix_to_match():
    prefix = "my-fake-prefix"
    environ["pipeline_name"] = prefix
    yield prefix
    del environ["pipeline_name"]


class TestPipelineComponent:
    def test_topic_substitution(self):
        pipeline_component = PlainPipelineComponent(
            name="test-pipeline-component",
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
                topic_name_config=TopicNameConfig(
                    default_error_topic_name="error-${component_type}",
                    default_output_topic_name="output-${component_type}",
                ),
            ),
            handlers=ComponentHandlers(
                schema_handler=MagicMock(),
                connector_handler=MagicMock(),
                topic_handler=MagicMock(),
            ),
            to=ToSection(
                models={},
                topics={
                    "${error_topic_name}": TopicConfig(
                        type=OutputTopicTypes.ERROR, partitions_count=10
                    ),
                    "${output_topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                },
            ),
        )

        assert pipeline_component.to
        assert "error-plain-pipeline-component" in pipeline_component.to.topics
        assert "output-plain-pipeline-component" in pipeline_component.to.topics
        assert len(pipeline_component.to.topics.keys()) == 2

    def test_prefix_substitution(self, prefix_to_match):
        pipeline_component = PlainPipelineComponent(
            name="test-pipeline-component",
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
                topic_name_config=TopicNameConfig(
                    default_error_topic_name="error-${component_type}",
                    default_output_topic_name="output-${component_type}",
                ),
            ),
            handlers=ComponentHandlers(
                schema_handler=MagicMock(),
                connector_handler=MagicMock(),
                topic_handler=MagicMock(),
            ),
        )
        assert prefix_to_match + "-" == pipeline_component.prefix
