from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from kpops.utils.yaml import load_yaml_file

RESOURCE_PATH = Path(__file__).parent / "resources"


def test_load_yaml():
    content = load_yaml_file(RESOURCE_PATH / "test.yaml")
    assert isinstance(content, dict)
    assert content["test"] == {"correct": "file"}


def test_fail_load_yaml():
    with pytest.raises(yaml.YAMLError):
        load_yaml_file(RESOURCE_PATH / "erroneous-file.yaml")


@patch("yaml.safe_load")
def test_caching_load_yaml(mocked_func):
    load_yaml_file(
        RESOURCE_PATH / "test.yaml",
        substitution={"example": "test", "another": "field"},
    )
    mocked_func.assert_called_once()
    mocked_func.reset_mock()

    # load the same yaml with the same substitution
    load_yaml_file(
        RESOURCE_PATH / "test.yaml",
        substitution={"example": "test", "another": "field"},
    )
    mocked_func.assert_not_called()
    mocked_func.reset_mock()

    # load the same yaml with the same substitution
    load_yaml_file(
        RESOURCE_PATH / "test.yaml",
        substitution={"another": "field", "example": "test"},
    )
    mocked_func.assert_not_called()
    mocked_func.reset_mock()

    # load the same yaml with the another substitution
    load_yaml_file(
        RESOURCE_PATH / "test.yaml",
        substitution={"another": "test"},
    )
    mocked_func.assert_called_once()
    mocked_func.reset_mock()

    # load the another yaml
    load_yaml_file(RESOURCE_PATH / "another-test.yaml")
    mocked_func.assert_called_once()
