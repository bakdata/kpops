from unittest.mock import patch

import pytest

from kpops.utils.environment import Environment


@pytest.fixture
def fake_environment_windows():
    return {"MY": "fake", "ENVIRONMENT": "here"}


@pytest.fixture
def fake_environment_linux():
    return {"my": "fake", "environment": "here"}


@patch("platform.system")
def test_normal_behaviour_get_item(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(fake_environment_linux)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_get_item_as_kwargs(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(**fake_environment_linux)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_keys_transformation(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(fake_environment_linux)
    keys = set(environment.keys())

    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_normal_behaviour_set_key(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(fake_environment_linux)
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_windows_behaviour_set_key(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(fake_environment_windows)
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_normal_behaviour_keys_transformation_kwargs(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(**fake_environment_linux)

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(fake_environment_windows)

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation_as_kwargs(
    system, fake_environment_windows
):
    system.return_value = "Windows"
    environment = Environment(**fake_environment_windows)
    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_get_item(system, fake_environment_windows):
    system.return_value = "Windows"

    environment = Environment(fake_environment_windows)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_windows_behaviour_get_item_as_kwargs(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(**fake_environment_windows)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"
