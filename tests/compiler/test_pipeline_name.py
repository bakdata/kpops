from pathlib import Path

import pytest

from kpops.config import KpopsConfig
from kpops.pipeline_generator.pipeline import Pipeline
from kpops.utils.environment import ENV

DEFAULTS_PATH = Path(__file__).parent / "resources"
PIPELINE_PATH = Path("./some/random/path/for/testing/pipeline.yaml")
DEFAULT_BASE_DIR = Path(".")


def test_should_set_pipeline_name_with_default_base_dir():
    Pipeline.set_pipeline_name_env_vars(DEFAULT_BASE_DIR, PIPELINE_PATH)

    assert "some-random-path-for-testing" == ENV["pipeline_name"]
    assert "some" == ENV["pipeline_name_0"]
    assert "random" == ENV["pipeline_name_1"]
    assert "path" == ENV["pipeline_name_2"]
    assert "for" == ENV["pipeline_name_3"]
    assert "testing" == ENV["pipeline_name_4"]


def test_should_set_pipeline_name_with_specific_relative_base_dir():
    Pipeline.set_pipeline_name_env_vars(Path("./some/random/path"), PIPELINE_PATH)

    assert "for-testing" == ENV["pipeline_name"]
    assert "for" == ENV["pipeline_name_0"]
    assert "testing" == ENV["pipeline_name_1"]


def test_should_set_pipeline_name_with_specific_absolute_base_dir():
    Pipeline.set_pipeline_name_env_vars(Path("some/random/path"), PIPELINE_PATH)

    assert "for-testing" == ENV["pipeline_name"]
    assert "for" == ENV["pipeline_name_0"]
    assert "testing" == ENV["pipeline_name_1"]


def test_should_set_pipeline_name_with_absolute_base_dir():
    Pipeline.set_pipeline_name_env_vars(Path.cwd(), PIPELINE_PATH)

    assert "some-random-path-for-testing" == ENV["pipeline_name"]
    assert "some" == ENV["pipeline_name_0"]
    assert "random" == ENV["pipeline_name_1"]
    assert "path" == ENV["pipeline_name_2"]
    assert "for" == ENV["pipeline_name_3"]
    assert "testing" == ENV["pipeline_name_4"]


def test_should_not_set_pipeline_name_with_the_same_base_dir():
    with pytest.raises(ValueError):
        Pipeline.set_pipeline_name_env_vars(PIPELINE_PATH, PIPELINE_PATH)


def test_pipeline_file_name_environment():
    config = KpopsConfig(
        defaults_path=DEFAULTS_PATH,
        environment="some_environment",
    )
    environment = Pipeline.pipeline_filename_environment(PIPELINE_PATH, config)
    assert environment.name == "pipeline_some_environment.yaml"
