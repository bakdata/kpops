import logging
from pathlib import Path

import pytest
import yaml
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

import kpops
from kpops.cli.main import app
from kpops.pipeline import ParsingException, ValidationError

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestPipeline:
    def test_python_api(self):
        pipeline = kpops.generate(
            RESOURCE_PATH / "first-pipeline" / "pipeline.yaml",
            defaults=RESOURCE_PATH,
        )
        assert len(pipeline) == 3

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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_generate_with_steps_flag_should_write_log_warning(
        self, caplog: pytest.LogCaptureFixture
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                str(RESOURCE_PATH / "first-pipeline/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
                "--steps",
                "a",
            ],
            catch_exceptions=False,
        )

        assert caplog.record_tuples == [
            (
                "root",
                logging.WARNING,
                "The following flags are considered only when `--template` is set: \n \
                '--steps'",
            )
        ]

        assert result.exit_code == 0, result.stdout

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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)

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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

            enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
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

        enriched_pipeline: dict = yaml.safe_load(result.stdout)

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
        with pytest.raises((ValueError, ParsingException)):
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
            ValidationError,
            match="step names should be unique. duplicate step names: resources-pipeline-duplicate-step-names-component",
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
        enriched_pipeline: dict = yaml.safe_load(result.stdout)
        assert (
            enriched_pipeline[0]["name"]
            == "in-order-to-have-len-fifty-two-name-should-end--here"
        )
