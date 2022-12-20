import os
from pathlib import Path

from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.utils.yaml_loading import load_yaml_file

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)


class TestPipeline:
    def test_load_pipeline(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "first-pipeline/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_pipelines_with_env_values(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "pipeline-with-envs/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_inflate_pipeline(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "pipeline-with-inflate/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_substitute_component_names(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "component-type-substitution/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))

        assert isinstance(enriched_pipeline, dict)
        labels = enriched_pipeline["components"][0]["app"]["labels"]
        assert labels["app_name"] == "scheduled-producer"
        assert labels["app_type"] == "scheduled-producer"

        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_no_input_topic(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "no-input-topic-pipeline/pipeline.yaml"),
                "tests.pipeline.test_components",
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_no_user_defined_components(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "no-user-defined-components/pipeline.yaml"),
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_kafka_connect_sink_weave_from_topics(self, tmpdir, snapshot):
        """Parse Connector topics from previous component to section."""
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")

    def test_with_env_defaults(self, tmpdir, snapshot):
        os.environ["KPOPS_ENVIRONMENT"] = "development"
        output_file_path = tmpdir.join("pipeline.yaml")
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "kafka-connect-sink/pipeline.yaml"),
                "--save",
                "--out-path",
                output_file_path,
                "--defaults",
                str(RESOURCE_PATH / "pipeline-with-env-defaults"),
            ],
        )

        assert result.exit_code == 0, result.exception

        enriched_pipeline = load_yaml_file(Path(output_file_path))
        snapshot.assert_match(enriched_pipeline, "test-pipeline")
