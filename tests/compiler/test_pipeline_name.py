from pathlib import Path

import pytest

from kpops.pipeline import PipelineGenerator
from kpops.utils.environment import ENV

DEFAULTS_PATH = Path(__file__).parent / "resources"
PIPELINE_PATH = Path("./some/random/path/for/testing/pipeline.yaml")
DEFAULT_BASE_DIR = Path()


def test_should_set_pipeline_name_with_default_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(DEFAULT_BASE_DIR, PIPELINE_PATH)

    assert ENV["pipeline_name"] == "some-random-path-for-testing"
    assert ENV["pipeline_name_0"] == "some"
    assert ENV["pipeline_name_1"] == "random"
    assert ENV["pipeline_name_2"] == "path"
    assert ENV["pipeline_name_3"] == "for"
    assert ENV["pipeline_name_4"] == "testing"


def test_should_set_pipeline_name_with_specific_relative_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(
        Path("./some/random/path"), PIPELINE_PATH
    )

    assert ENV["pipeline_name"] == "for-testing"
    assert ENV["pipeline_name_0"] == "for"
    assert ENV["pipeline_name_1"] == "testing"


def test_should_set_pipeline_name_with_specific_absolute_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(
        Path("some/random/path"), PIPELINE_PATH
    )

    assert ENV["pipeline_name"] == "for-testing"
    assert ENV["pipeline_name_0"] == "for"
    assert ENV["pipeline_name_1"] == "testing"


def test_should_set_pipeline_name_with_absolute_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(Path.cwd(), PIPELINE_PATH)

    assert ENV["pipeline_name"] == "some-random-path-for-testing"
    assert ENV["pipeline_name_0"] == "some"
    assert ENV["pipeline_name_1"] == "random"
    assert ENV["pipeline_name_2"] == "path"
    assert ENV["pipeline_name_3"] == "for"
    assert ENV["pipeline_name_4"] == "testing"


def test_should_not_set_pipeline_name_with_the_same_base_dir():
    with pytest.raises(
        ValueError, match="The pipeline-base-dir should not equal the pipeline-path"
    ):
        PipelineGenerator.set_pipeline_name_env_vars(PIPELINE_PATH, PIPELINE_PATH)


def test_pipeline_file_name_environment():
    environment = PipelineGenerator.pipeline_filename_environment(
        PIPELINE_PATH, "some_environment"
    )
    assert environment.name == "pipeline_some_environment.yaml"
