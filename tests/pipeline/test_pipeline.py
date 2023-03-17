from pathlib import Path

import yaml
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)


class TestPipeline:
    def test_load_pipeline(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "first-pipeline/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_name_equal_prefix_name_concatenation(self):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "name_prefix_concatenation/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)

        assert (
            enriched_pipeline["components"][0]["name"]
            == "my-fake-prefix-my-streams-app"
        )

    def test_pipelines_with_env_values(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "pipeline-with-envs/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_inflate_pipeline(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "pipeline-with-inflate/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_substitute_component_names(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "component-type-substitution/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)

        assert isinstance(enriched_pipeline, dict)
        labels = enriched_pipeline["components"][0]["app"]["labels"]
        assert labels["app_name"] == "scheduled-producer"
        assert labels["app_type"] == "scheduled-producer"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_no_input_topic(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "no-input-topic-pipeline/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_no_user_defined_components(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "no-user-defined-components/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_kafka_connect_sink_weave_from_topics(self, snapshot: SnapshotTest):
        """Parse Connector topics from previous component to section."""
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_env_defaults(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "pipeline-with-env-defaults"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_custom_config_with_relative_defaults_path(
        self, snapshot: SnapshotTest
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                str(RESOURCE_PATH / "custom-config/config.yaml"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        assert isinstance(enriched_pipeline, dict)

        producer_details = enriched_pipeline["components"][0]
        output_topic = producer_details["app"]["streams"]["outputTopic"]
        assert output_topic == "app1-test-topic"

        streams_app_details = enriched_pipeline["components"][1]
        output_topic = streams_app_details["app"]["streams"]["outputTopic"]
        assert output_topic == "app2-test-topic"
        error_topic = streams_app_details["app"]["streams"]["errorTopic"]
        assert error_topic == "app2-dead-letter-topic"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_custom_config_with_absolute_defaults_path(
        self, snapshot: SnapshotTest
    ):
        with open(
            str(RESOURCE_PATH / "custom-config/config.yaml"), "r"
        ) as rel_config_yaml:
            config_dict = yaml.safe_load(rel_config_yaml)
        defaults_path = (
            RESOURCE_PATH / "custom-config" / Path(config_dict["defaults_path"])
        )
        config_dict["defaults_path"] = str(defaults_path)
        temp_config_path = RESOURCE_PATH / "custom-config/temp_config.yaml"
        with open(str(temp_config_path), "w") as abs_config_yaml:
            try:
                yaml.dump(config_dict, abs_config_yaml)
                result = runner.invoke(
                    app,
                    [
                        "generate",
                        "--pipeline-base-dir",
                        PIPELINE_BASE_DIR,
                        str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                        "--config",
                        str(temp_config_path),
                    ],
                    catch_exceptions=False,
                )

                assert result.exit_code == 0

                enriched_pipeline = yaml.safe_load(result.stdout)
                assert isinstance(enriched_pipeline, dict)

                producer_details = enriched_pipeline["components"][0]
                output_topic = producer_details["app"]["streams"]["outputTopic"]
                assert output_topic == "app1-test-topic"

                streams_app_details = enriched_pipeline["components"][1]
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
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = yaml.safe_load(result.stdout)
        assert isinstance(enriched_pipeline, dict)

        producer_details = enriched_pipeline["components"][0]
        output_topic = producer_details["app"]["streams"]["outputTopic"]
        assert output_topic == "resources-custom-config-app1"

        streams_app_details = enriched_pipeline["components"][1]
        output_topic = streams_app_details["app"]["streams"]["outputTopic"]
        assert output_topic == "resources-custom-config-app2"
        error_topic = streams_app_details["app"]["streams"]["errorTopic"]
        assert error_topic == "resources-custom-config-app2-error"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")
