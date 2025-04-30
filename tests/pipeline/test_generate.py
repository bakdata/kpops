import asyncio
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from pytest_mock import MockerFixture
from pytest_snapshot.plugin import Snapshot
from typer.testing import CliRunner

import kpops.api as kpops
from kpops.api.options import FilterType
from kpops.cli.main import app
from kpops.component_handlers.kafka_connect.model import ConnectorNewState
from kpops.components.base_components.kafka_connector import KafkaSinkConnector
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp
from kpops.const.file_type import PIPELINE_YAML, KpopsFileType
from kpops.core.exception import ParsingException, ValidationError
from kpops.utils.environment import ENV

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures(
    "mock_env", "load_yaml_file_clear_cache", "custom_components", "clear_kpops_config"
)
class TestGenerate:
    @pytest.fixture(autouse=True)
    def log_info(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.api.log.info")

    def test_python_api(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML,
        )
        assert len(pipeline) == 3
        assert [component.type for component in pipeline.components] == [
            "scheduled-producer",
            "converter",
            "filter",
        ]

    def test_python_api_filter_include(self, log_info: MagicMock):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML,
            steps={"converter"},
            filter_type=FilterType.INCLUDE,
        )
        assert len(pipeline) == 1
        assert pipeline.components[0].type == "converter"
        assert log_info.call_count == 2
        log_info.assert_any_call("Picked up pipeline 'first-pipeline'")
        log_info.assert_any_call("Filtered pipeline:\n['converter']")

    def test_python_api_filter_exclude(self, log_info: MagicMock):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML,
            steps={"converter", "scheduled-producer"},
            filter_type=FilterType.EXCLUDE,
        )
        assert len(pipeline) == 1
        assert pipeline.components[0].type == "filter"
        assert log_info.call_count == 2
        log_info.assert_any_call("Picked up pipeline 'first-pipeline'")
        log_info.assert_any_call(
            "Filtered pipeline:\n['a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name']"
        )

    def test_load_pipeline(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_load_yaml_clear_env(self) -> None:
        kpops.generate(RESOURCE_PATH / "pipeline-folders/pipeline-1/pipeline.yaml")
        assert ENV["pipeline.name_2"] == "pipeline-1"
        kpops.generate(RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML)
        assert "pipeline.name_2" not in ENV

    def test_load_pipeline_with_folder_path(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-folders"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, "pipeline.yaml")

    def test_load_pipeline_with_multiple_pipeline_paths(self, snapshot: Snapshot):
        path_1 = RESOURCE_PATH / "pipeline-folders/pipeline-1/pipeline.yaml"
        path_2 = RESOURCE_PATH / "pipeline-folders/pipeline-2/pipeline.yaml"
        path_3 = RESOURCE_PATH / "pipeline-folders/pipeline-3/pipeline.yaml"
        result = runner.invoke(
            app,
            ["generate", str(path_1), str(path_2), str(path_3)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, "pipeline.yaml")

    def test_name_equal_prefix_name_concatenation(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "name_prefix_concatenation" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)

        assert enriched_pipeline[0]["prefix"] == "my-fake-prefix-"
        assert enriched_pipeline[0]["name"] == "my-streams-app"

    def test_pipelines_with_envs(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-envs" / PIPELINE_YAML),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_inflate_pipeline(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-inflate" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_substitute_in_component(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "component-type-substitution" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["prefix"] == "resources-component-type-substitution-"
        )
        assert enriched_pipeline[0]["name"] == "scheduled-producer"

        labels = enriched_pipeline[0]["values"]["labels"]
        assert labels["app_name"] == "scheduled-producer"
        assert labels["app_type"] == "scheduled-producer"
        assert labels["app_schedule"] == "30 3/8 * * *"
        assert (
            enriched_pipeline[2]["values"]["labels"]["app_resources_requests_memory"]
            == "3G"
        )
        assert (
            "resources-component-type-substitution-scheduled-producer"
            in enriched_pipeline[0]["to"]["topics"]
        )
        assert (
            "resources-component-type-substitution-converter-error"
            in enriched_pipeline[1]["to"]["topics"]
        )
        assert (
            enriched_pipeline[2]["values"]["labels"]["test_placeholder_in_placeholder"]
            == "filter-app-filter"
        )

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    @pytest.mark.timeout(2)
    def test_substitute_in_component_infinite_loop(self):
        with pytest.raises((ValueError, ParsingException)):
            runner.invoke(
                app,
                [
                    "generate",
                    str(
                        RESOURCE_PATH
                        / "component-type-substitution"
                        / KpopsFileType.PIPELINE.as_yaml_file(prefix="infinite_"),
                    ),
                ],
                catch_exceptions=False,
            )

    def test_kafka_connector_config_parsing(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "kafka-connect-sink-config" / PIPELINE_YAML,
            config=RESOURCE_PATH / "kafka-connect-sink-config",
        )
        assert len(pipeline) == 1
        sink_connector = pipeline.components[0]
        assert isinstance(sink_connector, KafkaSinkConnector)
        assert sink_connector.state is ConnectorNewState.PAUSED
        sink_connector = sink_connector.generate()
        assert sink_connector["state"] == "paused"
        assert (
            sink_connector["config"]["errors.deadletterqueue.topic.name"]
            == "kafka-sink-connector-error-topic"
        )

    def test_no_input_topic(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "no-input-topic-pipeline" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_no_user_defined_components(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "no-user-defined-components" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_kafka_connect_sink_weave_from_topics(self, snapshot: Snapshot):
        """Parse Connector topics from previous component to section."""
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "kafka-connect-sink" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_read_from_component(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "read-from-component" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_with_env_defaults(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-env-defaults" / PIPELINE_YAML),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_prefix_pipeline_component(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(
                    RESOURCE_PATH
                    / "pipeline-component-should-have-prefix"
                    / PIPELINE_YAML,
                ),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_with_custom_config_with_relative_defaults_path(
        self,
        snapshot: Snapshot,
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        producer_details = enriched_pipeline[0]
        output_topic = producer_details["values"]["kafka"]["outputTopic"]
        assert output_topic == "app1-test-topic"

        streams_app_details = enriched_pipeline[1]
        output_topic = streams_app_details["values"]["kafka"]["outputTopic"]
        assert output_topic == "app2-test-topic"
        error_topic = streams_app_details["values"]["kafka"]["errorTopic"]
        assert error_topic == "app2-dead-letter-topic"

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_with_custom_config_with_absolute_defaults_path(
        self,
        snapshot: Snapshot,
    ):
        with Path(RESOURCE_PATH / "custom-config/config.yaml").open(
            "r",
        ) as rel_config_yaml:
            config_dict: dict[str, Any] = yaml.safe_load(rel_config_yaml)
        config_dict["defaults_path"] = str(
            (RESOURCE_PATH / "no-topics-defaults").absolute(),
        )
        temp_config_path = RESOURCE_PATH / "custom-config/config_custom.yaml"
        try:
            with temp_config_path.open("w") as abs_config_yaml:
                yaml.safe_dump(config_dict, abs_config_yaml)
            result = runner.invoke(
                app,
                [
                    "generate",
                    str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                    "--config",
                    str(temp_config_path.parent),
                    "--environment",
                    "development",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0, result.stdout

            enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
            producer_details = enriched_pipeline[0]
            output_topic = producer_details["values"]["kafka"]["outputTopic"]
            assert output_topic == "app1-test-topic"

            streams_app_details = enriched_pipeline[1]
            output_topic = streams_app_details["values"]["kafka"]["outputTopic"]
            assert output_topic == "app2-test-topic"
            error_topic = streams_app_details["values"]["kafka"]["errorTopic"]
            assert error_topic == "app2-dead-letter-topic"

            snapshot.assert_match(result.stdout, PIPELINE_YAML)
        finally:
            temp_config_path.unlink()

    def test_default_config(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        producer_details = enriched_pipeline[0]
        output_topic = producer_details["values"]["kafka"]["outputTopic"]
        assert output_topic == "resources-custom-config-app1"

        streams_app_details = enriched_pipeline[1]
        output_topic = streams_app_details["values"]["kafka"]["outputTopic"]
        assert output_topic == "resources-custom-config-app2"
        error_topic = streams_app_details["values"]["kafka"]["errorTopic"]
        assert error_topic == "resources-custom-config-app2-error"

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_env_vars_precedence_over_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(name="KPOPS_KAFKA_BROKERS", value="env_broker")

        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["values"]["kafka"]["bootstrapServers"] == "env_broker"
        )

    def test_nested_config_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            name="KPOPS_SCHEMA_REGISTRY__URL", value="http://somename:1234"
        )

        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["values"]["kafka"]["schemaRegistryUrl"]
            == "http://somename:1234/"
        )

    def test_env_specific_config_env_def_in_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv(name="KPOPS_ENVIRONMENT", value="production")
        config_path = str(RESOURCE_PATH / "multi-config")
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                config_path,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["values"]["kafka"]["schemaRegistryUrl"]
            == "http://production:8081/"
        )

    @pytest.mark.parametrize(
        ("config_dir", "expected_url"),
        [
            pytest.param("multi-config", "http://production:8081/", id="multi-config"),
            pytest.param(
                "env-specific-config-only",
                "http://localhost:8081/",
                id="env-specific-config-only",
            ),
        ],
    )
    def test_env_specific_config_env_def_in_cli(
        self, config_dir: str, expected_url: str
    ):
        config_path = str(RESOURCE_PATH / config_dir)
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                config_path,
                "--environment",
                "production",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["values"]["kafka"]["schemaRegistryUrl"] == expected_url
        )

    def test_config_dir_doesnt_exist(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                "./non-existent-dir",
                "--environment",
                "production",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code != 0

    def test_model_serialization(self, snapshot: Snapshot):
        """Test model serialization of component containing pathlib.Path attribute."""
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-paths" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, PIPELINE_YAML)

    def test_dotenv_support(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config" / PIPELINE_YAML),
                "--config",
                str(RESOURCE_PATH / "dotenv"),
                "--dotenv",
                str(RESOURCE_PATH / "dotenv/.env"),
                "--dotenv",
                str(RESOURCE_PATH / "dotenv/custom.env"),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[1]["values"]["kafka"]["schemaRegistryUrl"]
            == "http://notlocalhost:8081/"
        )

    def test_short_topic_definition(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-short-topics" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)

        output_topics = enriched_pipeline[4]["to"]["topics"]
        input_topics = enriched_pipeline[4]["from"]["topics"]
        input_components = enriched_pipeline[4]["from"]["components"]
        assert "type" not in output_topics["output-topic"]
        assert output_topics["error-topic"]["type"] == "error"
        assert "type" not in output_topics["extra-topic-output"]
        assert "label" not in output_topics["output-topic"]
        assert "label" not in output_topics["error-topic"]
        assert output_topics["extra-topic-output"]["label"] == "role"

        assert "type" not in ["input-topic"]
        assert "type" not in input_topics["extra-topic"]
        assert input_topics["input-pattern"]["type"] == "pattern"
        assert input_topics["extra-pattern"]["type"] == "pattern"
        assert "label" not in input_topics["input-topic"]
        assert "label" not in input_topics["input-pattern"]
        assert input_topics["extra-topic"]["label"] == "role"
        assert input_topics["extra-pattern"]["label"] == "role"

        assert "type" not in input_components["component-input"]
        assert "type" not in input_components["component-extra"]
        assert input_components["component-input-pattern"]["type"] == "pattern"
        assert input_components["component-extra-pattern"]["type"] == "pattern"
        assert "label" not in input_components["component-input"]
        assert "label" not in input_components["component-input-pattern"]
        assert input_components["component-extra"]["label"] == "role"
        assert input_components["component-extra-pattern"]["label"] == "role"

    def test_kubernetes_app_name_validation(self):
        with (
            pytest.raises(
                ParsingException,
                match="Error enriching filter component illegal_name",
            ),
            pytest.raises(
                ValueError,
                match="The component name illegal_name is invalid for Kubernetes.",
            ),
        ):
            runner.invoke(
                app,
                [
                    "generate",
                    str(
                        RESOURCE_PATH
                        / "pipeline-with-illegal-kubernetes-name"
                        / PIPELINE_YAML,
                    ),
                ],
                catch_exceptions=False,
            )

    def test_validate_unique_step_names(self):
        with (
            pytest.raises(
                ParsingException,
                match="Error enriching pipeline-component component component",
            ),
            pytest.raises(
                ValidationError,
                match="Pipeline steps must have unique id, 'component-resources-pipeline-duplicate-step-names-component' already exists.",
            ),
        ):
            runner.invoke(
                app,
                [
                    "generate",
                    str(
                        RESOURCE_PATH / "pipeline-duplicate-step-names" / PIPELINE_YAML
                    ),
                ],
                catch_exceptions=False,
            )

    def test_validate_loops_on_pipeline(self):
        with pytest.raises(ValueError, match="Pipeline is not a valid DAG."):
            runner.invoke(
                app,
                [
                    "generate",
                    str(RESOURCE_PATH / "pipeline-with-loop" / PIPELINE_YAML),
                ],
                catch_exceptions=False,
            )

    def test_validate_simple_graph(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "pipelines-with-graphs" / "simple-pipeline" / PIPELINE_YAML,
        )
        assert len(pipeline.components) == 2
        assert len(pipeline._graph.nodes) == 3
        assert len(pipeline._graph.edges) == 2
        topic_nodes = [
            node for node in pipeline._graph.nodes if node.startswith("topic-")
        ]
        assert len(topic_nodes) == 1
        assert len(pipeline.components) == len(pipeline._graph.nodes) - len(topic_nodes)

    def test_validate_topic_and_component_same_name(self):
        pipeline = kpops.generate(
            RESOURCE_PATH
            / "pipelines-with-graphs"
            / "same-topic-and-component-name"
            / PIPELINE_YAML,
        )
        component, topic = list(pipeline._graph.nodes)
        edges = list(pipeline._graph.edges)
        assert component == topic.removeprefix("topic-")
        assert (component, topic) in edges

    async def test_parallel_execution_graph(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline" / PIPELINE_YAML,
            config=RESOURCE_PATH / "parallel-pipeline",
        )

        called_component = AsyncMock()

        sleep_table_components = {
            "transaction-avro-producer-1": 1,
            "transaction-avro-producer-2": 0,
            "transaction-avro-producer-3": 2,
            "transaction-joiner": 3,
            "fraud-detector": 2,
            "account-linker": 0,
            "s3-connector-1": 2,
            "s3-connector-2": 1,
            "s3-connector-3": 0,
        }

        async def name_runner(component: PipelineComponent):
            await asyncio.sleep(sleep_table_components[component.name])
            await called_component(component.name)

        execution_graph = pipeline.build_execution_graph(name_runner)

        await execution_graph

        assert called_component.mock_calls == [
            mock.call("transaction-avro-producer-2"),
            mock.call("transaction-avro-producer-1"),
            mock.call("transaction-avro-producer-3"),
            mock.call("transaction-joiner"),
            mock.call("fraud-detector"),
            mock.call("account-linker"),
            mock.call("s3-connector-3"),
            mock.call("s3-connector-2"),
            mock.call("s3-connector-1"),
        ]

    async def test_subgraph_execution(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline" / PIPELINE_YAML,
            config=RESOURCE_PATH / "parallel-pipeline",
        )

        called_component = AsyncMock()

        async def name_runner(component: PipelineComponent):
            await called_component(component.name)

        pipeline.remove(pipeline.components[8].id)
        pipeline.remove(pipeline.components[7].id)
        pipeline.remove(pipeline.components[5].id)
        pipeline.remove(pipeline.components[4].id)
        pipeline.remove(pipeline.components[2].id)
        pipeline.remove(pipeline.components[1].id)
        execution_graph = pipeline.build_execution_graph(name_runner)

        await execution_graph

        assert called_component.mock_calls == [
            mock.call("transaction-avro-producer-1"),
            mock.call("transaction-joiner"),
            mock.call("s3-connector-1"),
        ]

    async def test_parallel_execution_graph_reverse(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline" / PIPELINE_YAML,
            config=RESOURCE_PATH / "parallel-pipeline",
        )

        called_component = AsyncMock()

        sleep_table_components = {
            "transaction-avro-producer-1": 1,
            "transaction-avro-producer-2": 0,
            "transaction-avro-producer-3": 2,
            "transaction-joiner": 3,
            "fraud-detector": 2,
            "account-linker": 0,
            "s3-connector-1": 2,
            "s3-connector-2": 1,
            "s3-connector-3": 0,
        }

        async def name_runner(component: PipelineComponent):
            await asyncio.sleep(sleep_table_components[component.name])
            await called_component(component.name)

        execution_graph = pipeline.build_execution_graph(name_runner, reverse=True)

        await execution_graph

        assert called_component.mock_calls == [
            mock.call("s3-connector-3"),
            mock.call("s3-connector-2"),
            mock.call("s3-connector-1"),
            mock.call("account-linker"),
            mock.call("fraud-detector"),
            mock.call("transaction-joiner"),
            mock.call("transaction-avro-producer-2"),
            mock.call("transaction-avro-producer-1"),
            mock.call("transaction-avro-producer-3"),
        ]

    def test_temp_trim_release_name(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "temp-trim-release-name" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list[dict[str, Any]] = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["name"]
            == "in-order-to-have-len-fifty-two-name-should-end--here"
        )

    def test_substitution_in_inflated_component(self):
        pipeline = kpops.generate(RESOURCE_PATH / "resetter_values" / PIPELINE_YAML)
        assert isinstance(pipeline.components[1], KafkaSinkConnector)
        assert (
            pipeline.components[1]._resetter.values.label == "inflated-connector-name"  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        )
        assert (
            pipeline.components[1]._resetter.values.imageTag  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            == "override-default-image-tag"
        )

    def test_substitution_in_resetter(self):
        pipeline = kpops.generate(
            RESOURCE_PATH
            / "resetter_values"
            / KpopsFileType.PIPELINE.as_yaml_file(suffix="_connector_only"),
        )
        assert isinstance(pipeline.components[0], KafkaSinkConnector)
        assert pipeline.components[0].name == "es-sink-connector"
        assert pipeline.components[0]._resetter.name == "es-sink-connector"
        assert pipeline.components[0]._resetter.values.label == "es-sink-connector"  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        assert (
            pipeline.components[0]._resetter.values.imageTag  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            == "override-default-image-tag"
        )

    def test_streams_bootstrap(self, snapshot: Snapshot):
        pipeline = kpops.generate(
            RESOURCE_PATH / "streams-bootstrap" / PIPELINE_YAML,
        )

        cleaner_diff_config = [("cleaner",)]
        producer_app = pipeline.components[0]
        assert isinstance(producer_app, ProducerApp)
        assert not producer_app.diff_config.ignore
        assert producer_app._cleaner.diff_config.ignore == cleaner_diff_config

        streams_app = pipeline.components[1]
        assert isinstance(streams_app, StreamsApp)
        assert streams_app.diff_config.ignore == [("foo", "bar")]
        assert streams_app._cleaner.diff_config.ignore == cleaner_diff_config

        snapshot.assert_match(pipeline.to_yaml(), PIPELINE_YAML)

    def test_symlinked_pipeline_as_original_pipeline(
        self,
    ):
        pipeline_original = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / PIPELINE_YAML,
        )
        pipeline_symlinked = kpops.generate(
            RESOURCE_PATH / "pipeline-symlinked" / PIPELINE_YAML,
        )

        assert pipeline_original.to_yaml() == pipeline_symlinked.to_yaml()

    @pytest.mark.skip(  # FIXME
        reason="pipeline folder is currently CLI-only feature, cannot test this using current API method"
    )
    def test_symlinked_folder_renders_as_original_folder_pipeline(
        self,
    ):
        pipeline_original = kpops.generate(
            RESOURCE_PATH / "first-pipeline",
        )
        pipeline_symlinked = kpops.generate(
            RESOURCE_PATH / "symlinked-folder",
        )

        assert pipeline_original == pipeline_symlinked

    @pytest.mark.skip(  # FIXME
        reason="pipeline folder is currently CLI-only feature, cannot test this using current API method"
    )
    def test_symlinked_folder_and_pipelines_with_normal_pipeline_render_as_original(
        self,
    ):
        pipeline_original = kpops.generate(
            RESOURCE_PATH / "pipeline-folders",
        )
        pipeline_symlinked = kpops.generate(
            RESOURCE_PATH / "pipeline-folders-with-symlinks",
        )

        assert pipeline_original == pipeline_symlinked
