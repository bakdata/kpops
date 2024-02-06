import asyncio
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from pytest_mock import MockerFixture
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

import kpops
from kpops.cli.main import FilterType, app
from kpops.components import KafkaSinkConnector, PipelineComponent
from kpops.pipeline import ParsingException, ValidationError

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestGenerate:
    @pytest.fixture(autouse=True)
    def log_info(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.cli.main.log.info")

    def test_python_api(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / "pipeline.yaml",
            defaults=RESOURCE_PATH,
            output=False,
        )
        assert len(pipeline) == 3
        assert [component.type for component in pipeline.components] == [
            "scheduled-producer",
            "converter",
            "filter",
        ]

    def test_python_api_filter_include(self, log_info: MagicMock):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / "pipeline.yaml",
            defaults=RESOURCE_PATH,
            output=False,
            steps="converter",
            filter_type=FilterType.INCLUDE,
        )
        assert len(pipeline) == 1
        assert pipeline.components[0].type == "converter"
        assert log_info.call_count == 1
        log_info.assert_any_call("Filtered pipeline:\n['converter']")

    def test_python_api_filter_exclude(self, log_info: MagicMock):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / "pipeline.yaml",
            defaults=RESOURCE_PATH,
            output=False,
            steps="converter,scheduled-producer",
            filter_type=FilterType.EXCLUDE,
        )
        assert len(pipeline) == 1
        assert pipeline.components[0].type == "filter"
        assert log_info.call_count == 1
        log_info.assert_any_call(
            "Filtered pipeline:\n['a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name']"
        )

    def test_load_pipeline(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "first-pipeline/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_name_equal_prefix_name_concatenation(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "name_prefix_concatenation/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)

        assert enriched_pipeline[0]["prefix"] == "my-fake-prefix-"
        assert enriched_pipeline[0]["name"] == "my-streams-app"

    def test_pipelines_with_env_values(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-envs/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_inflate_pipeline(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-inflate/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_substitute_in_component(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "component-type-substitution/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["prefix"] == "resources-component-type-substitution-"
        )
        assert enriched_pipeline[0]["name"] == "scheduled-producer"

        labels = enriched_pipeline[0]["app"]["labels"]
        assert labels["app_name"] == "scheduled-producer"
        assert labels["app_type"] == "scheduled-producer"
        assert labels["app_schedule"] == "30 3/8 * * *"
        assert (
            enriched_pipeline[2]["app"]["labels"]["app_resources_requests_memory"]
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
            enriched_pipeline[2]["app"]["labels"]["test_placeholder_in_placeholder"]
            == "filter-app-filter"
        )

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    @pytest.mark.timeout(2)
    def test_substitute_in_component_infinite_loop(self):
        with pytest.raises((ValueError, ParsingException)):
            runner.invoke(
                app,
                [
                    "generate",
                    str(
                        RESOURCE_PATH
                        / "component-type-substitution/infinite_pipeline.yaml",
                    ),
                    "--defaults",
                    str(RESOURCE_PATH),
                ],
                catch_exceptions=False,
            )

    def test_kafka_connector_config_parsing(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "kafka-connect-sink-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
                "--config",
                str(RESOURCE_PATH / "kafka-connect-sink-config"),
            ],
            catch_exceptions=False,
        )
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        sink_connector = enriched_pipeline[0]
        assert (
            sink_connector["app"]["errors.deadletterqueue.topic.name"]
            == "kafka-sink-connector-error-topic"
        )

    def test_no_input_topic(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "no-input-topic-pipeline/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_no_user_defined_components(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "no-user-defined-components/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_kafka_connect_sink_weave_from_topics(self, snapshot: SnapshotTest):
        """Parse Connector topics from previous component to section."""
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_read_from_component(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "read-from-component/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_env_defaults(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "pipeline-with-env-defaults"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_prefix_pipeline_component(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(
                    RESOURCE_PATH
                    / "pipeline-component-should-have-prefix/pipeline.yaml",
                ),
                "--defaults",
                str(RESOURCE_PATH / "pipeline-component-should-have-prefix"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_custom_config_with_relative_defaults_path(
        self,
        snapshot: SnapshotTest,
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        producer_details = enriched_pipeline[0]
        output_topic = producer_details["app"]["streams"]["outputTopic"]
        assert output_topic == "app1-test-topic"

        streams_app_details = enriched_pipeline[1]
        output_topic = streams_app_details["app"]["streams"]["outputTopic"]
        assert output_topic == "app2-test-topic"
        error_topic = streams_app_details["app"]["streams"]["errorTopic"]
        assert error_topic == "app2-dead-letter-topic"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_custom_config_with_absolute_defaults_path(
        self,
        snapshot: SnapshotTest,
    ):
        with Path(RESOURCE_PATH / "custom-config/config.yaml").open(
            "r",
        ) as rel_config_yaml:
            config_dict: dict = yaml.safe_load(rel_config_yaml)
        config_dict["defaults_path"] = str(
            (RESOURCE_PATH / "no-topics-defaults").absolute(),
        )
        temp_config_path = RESOURCE_PATH / "custom-config/config_custom.yaml"
        try:
            with temp_config_path.open("w") as abs_config_yaml:
                yaml.dump(config_dict, abs_config_yaml)
            result = runner.invoke(
                app,
                [
                    "generate",
                    str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                    "--config",
                    str(temp_config_path.parent),
                    "--environment",
                    "development",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0, result.stdout

            enriched_pipeline: list = yaml.safe_load(result.stdout)
            producer_details = enriched_pipeline[0]
            output_topic = producer_details["app"]["streams"]["outputTopic"]
            assert output_topic == "app1-test-topic"

            streams_app_details = enriched_pipeline[1]
            output_topic = streams_app_details["app"]["streams"]["outputTopic"]
            assert output_topic == "app2-test-topic"
            error_topic = streams_app_details["app"]["streams"]["errorTopic"]
            assert error_topic == "app2-dead-letter-topic"

            snapshot.assert_match(enriched_pipeline, "test-pipeline")
        finally:
            temp_config_path.unlink()

    def test_default_config(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        producer_details = enriched_pipeline[0]
        output_topic = producer_details["app"]["streams"]["outputTopic"]
        assert output_topic == "resources-custom-config-app1"

        streams_app_details = enriched_pipeline[1]
        output_topic = streams_app_details["app"]["streams"]["outputTopic"]
        assert output_topic == "resources-custom-config-app2"
        error_topic = streams_app_details["app"]["streams"]["errorTopic"]
        assert error_topic == "resources-custom-config-app2-error"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_env_vars_precedence_over_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(name="KPOPS_KAFKA_BROKERS", value="env_broker")

        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert enriched_pipeline[0]["app"]["streams"]["brokers"] == "env_broker"

    def test_nested_config_env_vars(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            name="KPOPS_SCHEMA_REGISTRY__URL", value="http://somename:1234"
        )

        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["app"]["streams"]["schemaRegistryUrl"]
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
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                config_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["app"]["streams"]["schemaRegistryUrl"]
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
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                config_path,
                "--defaults",
                str(RESOURCE_PATH),
                "--environment",
                "production",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["app"]["streams"]["schemaRegistryUrl"] == expected_url
        )

    def test_config_dir_doesnt_exist(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                "./non-existent-dir",
                "--defaults",
                str(RESOURCE_PATH),
                "--environment",
                "production",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code != 0

    def test_model_serialization(self, snapshot: SnapshotTest):
        """Test model serialization of component containing pathlib.Path attribute."""
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-paths/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_dotenv_support(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
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

        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[1]["app"]["streams"]["schemaRegistryUrl"]
            == "http://notlocalhost:8081/"
        )

    def test_short_topic_definition(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "pipeline-with-short-topics/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "pipeline-with-short-topics"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: list = yaml.safe_load(result.stdout)

        output_topics = enriched_pipeline[4]["to"]["topics"]
        input_topics = enriched_pipeline[4]["from"]["topics"]
        input_components = enriched_pipeline[4]["from"]["components"]
        assert "type" not in output_topics["output-topic"]
        assert output_topics["error-topic"]["type"] == "error"
        assert "type" not in output_topics["extra-topic-output"]
        assert "role" not in output_topics["output-topic"]
        assert "role" not in output_topics["error-topic"]
        assert output_topics["extra-topic-output"]["role"] == "role"

        assert "type" not in ["input-topic"]
        assert "type" not in input_topics["extra-topic"]
        assert input_topics["input-pattern"]["type"] == "pattern"
        assert input_topics["extra-pattern"]["type"] == "pattern"
        assert "role" not in input_topics["input-topic"]
        assert "role" not in input_topics["input-pattern"]
        assert input_topics["extra-topic"]["role"] == "role"
        assert input_topics["extra-pattern"]["role"] == "role"

        assert "type" not in input_components["component-input"]
        assert "type" not in input_components["component-extra"]
        assert input_components["component-input-pattern"]["type"] == "pattern"
        assert input_components["component-extra-pattern"]["type"] == "pattern"
        assert "role" not in input_components["component-input"]
        assert "role" not in input_components["component-input-pattern"]
        assert input_components["component-extra"]["role"] == "role"
        assert input_components["component-extra-pattern"]["role"] == "role"

    def test_kubernetes_app_name_validation(self):
        with pytest.raises(
            ParsingException,
            match="Error enriching filter component illegal_name",
        ), pytest.raises(
            ValueError,
            match="The component name illegal_name is invalid for Kubernetes.",
        ):
            runner.invoke(
                app,
                [
                    "generate",
                    str(
                        RESOURCE_PATH
                        / "pipeline-with-illegal-kubernetes-name/pipeline.yaml",
                    ),
                    "--defaults",
                    str(RESOURCE_PATH),
                ],
                catch_exceptions=False,
            )

    def test_validate_unique_step_names(self):
        with pytest.raises(
            ParsingException,
            match="Error enriching pipeline-component component component",
        ), pytest.raises(
            ValidationError,
            match="Pipeline steps must have unique id, 'component-resources-pipeline-duplicate-step-names-component' already exists.",
        ):
            runner.invoke(
                app,
                [
                    "generate",
                    str(RESOURCE_PATH / "pipeline-duplicate-step-names/pipeline.yaml"),
                    "--defaults",
                    str(RESOURCE_PATH),
                ],
                catch_exceptions=False,
            )

    def test_validate_loops_on_pipeline(self):
        with pytest.raises(ValueError, match="Pipeline is not a valid DAG."):
            runner.invoke(
                app,
                [
                    "generate",
                    str(RESOURCE_PATH / "pipeline-with-loop/pipeline.yaml"),
                    "--defaults",
                    str(RESOURCE_PATH / "pipeline-with-loop"),
                ],
                catch_exceptions=False,
            )

    def test_validate_simple_graph(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "pipelines-with-graphs/simple-pipeline/pipeline.yaml",
            defaults=RESOURCE_PATH / "pipelines-with-graphs" / "simple-pipeline",
        )
        assert len(pipeline.components) == 2
        assert len(pipeline.graph.nodes) == 3
        assert len(pipeline.graph.edges) == 2
        node_components = list(
            filter(lambda node_id: "component" in node_id, pipeline.graph.nodes)
        )
        assert len(pipeline.components) == len(node_components)

    def test_validate_topic_and_component_same_name(self):
        pipeline = kpops.generate(
            RESOURCE_PATH
            / "pipelines-with-graphs/same-topic-and-component-name/pipeline.yaml",
            defaults=RESOURCE_PATH
            / "pipelines-with-graphs"
            / "same-topic-and-component-name",
        )
        component, topic = list(pipeline.graph.nodes)
        edges = list(pipeline.graph.edges)
        assert component == f"component-{topic}"
        assert (component, topic) in edges

    @pytest.mark.asyncio()
    async def test_parallel_execution_graph(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline/pipeline.yaml",
            defaults=RESOURCE_PATH / "parallel-pipeline",
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

    @pytest.mark.asyncio()
    async def test_subgraph_execution(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline/pipeline.yaml",
            defaults=RESOURCE_PATH / "parallel-pipeline",
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
            mock.call("s3-connector-1"),
            mock.call("transaction-joiner"),
        ]

    @pytest.mark.asyncio()
    async def test_parallel_execution_graph_reverse(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "parallel-pipeline/pipeline.yaml",
            defaults=RESOURCE_PATH / "parallel-pipeline",
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
                str(RESOURCE_PATH / "temp-trim-release-name/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "temp-trim-release-name"),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["name"]
            == "in-order-to-have-len-fifty-two-name-should-end--here"
        )

    def test_substitution_in_inflated_component(self):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "resetter_values/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "resetter_values"),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        enriched_pipeline: list = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[1]["_resetter"]["app"]["label"]
            == "inflated-connector-name"
        )

    def test_substitution_in_resetter(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "resetter_values/pipeline_connector_only.yaml",
            defaults=RESOURCE_PATH / "resetter_values",
        )
        assert isinstance(pipeline.components[0], KafkaSinkConnector)
        assert pipeline.components[0].name == "es-sink-connector"
        assert pipeline.components[0]._resetter.name == "es-sink-connector"
        assert hasattr(pipeline.components[0]._resetter.app, "label")
        assert pipeline.components[0]._resetter.app.label == "es-sink-connector"

        enriched_pipeline: list = yaml.safe_load(pipeline.to_yaml())
        assert enriched_pipeline[0]["name"] == "es-sink-connector"
        assert enriched_pipeline[0]["_resetter"]["name"] == "es-sink-connector"
        assert enriched_pipeline[0]["_resetter"]["app"]["label"] == "es-sink-connector"
