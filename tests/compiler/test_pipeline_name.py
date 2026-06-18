from pathlib import Path

import pytest

from kpops.const.file_type import KpopsFileType
from kpops.pipeline import PipelineGenerator
from kpops.utils.environment import ENV

PIPELINE_PATH = (
    Path("./some/random/path/for/testing") / KpopsFileType.PIPELINE.as_yaml_file()
)

PIPELINE_BASE_DIR = Path()


def test_should_set_pipeline_name_with_default_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(PIPELINE_BASE_DIR, PIPELINE_PATH)

    assert ENV["pipeline.name"] == "some-random-path-for-testing"
    assert ENV["pipeline.parent.name"] == "some-random-path-for"
    assert ENV["pipeline.name_0"] == "some"
    assert ENV["pipeline.name_1"] == "random"
    assert ENV["pipeline.name_2"] == "path"
    assert ENV["pipeline.name_3"] == "for"
    assert ENV["pipeline.name_4"] == "testing"


def test_should_set_pipeline_name_with_specific_relative_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(
        Path("./some/random/path"), PIPELINE_PATH
    )

    assert ENV["pipeline.name"] == "for-testing"
    assert ENV["pipeline.parent.name"] == "for"
    assert ENV["pipeline.name_0"] == "for"
    assert ENV["pipeline.name_1"] == "testing"


def test_should_set_pipeline_name_with_specific_absolute_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(
        Path("some/random/path"), PIPELINE_PATH
    )

    assert ENV["pipeline.name"] == "for-testing"
    assert ENV["pipeline.parent.name"] == "for"
    assert ENV["pipeline.name_0"] == "for"
    assert ENV["pipeline.name_1"] == "testing"


def test_should_set_pipeline_name_with_absolute_base_dir():
    PipelineGenerator.set_pipeline_name_env_vars(Path.cwd(), PIPELINE_PATH)

    assert ENV["pipeline.name"] == "some-random-path-for-testing"
    assert ENV["pipeline.parent.name"] == "some-random-path-for"
    assert ENV["pipeline.name_0"] == "some"
    assert ENV["pipeline.name_1"] == "random"
    assert ENV["pipeline.name_2"] == "path"
    assert ENV["pipeline.name_3"] == "for"
    assert ENV["pipeline.name_4"] == "testing"


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
