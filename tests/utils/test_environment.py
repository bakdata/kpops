import os
from unittest.mock import patch

import pytest

from kpops.utils.environment import Environment


@pytest.fixture()
def fake_environment_windows(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MY", "fake")
    monkeypatch.setenv("ENVIRONMENT", "here")


@pytest.fixture()
def fake_environment_linux(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("my", "fake")
    monkeypatch.setenv("environment", "here")


@patch("platform.system")
def test_normal_behaviour_get_item(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(os.environ)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_update_parent_item(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(os.environ)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"
    with pytest.raises(KeyError):
        environment["test"]
    os.environ["TEST"] = "test"
    assert environment["test"] == "test"


@patch("platform.system")
def test_normal_behaviour_get_item_as_kwargs(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(**os.environ)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_keys_transformation(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(os.environ)
    keys = set(environment.keys())

    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_normal_behaviour_set_key(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(os.environ)
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_windows_behaviour_set_key(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(os.environ)
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_normal_behaviour_keys_transformation_kwargs(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(**os.environ)

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(os.environ)

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation_as_kwargs(
    system, fake_environment_windows
):
    system.return_value = "Windows"
    environment = Environment(**os.environ)
    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_get_item(system, fake_environment_windows):
    system.return_value = "Windows"

    environment = Environment(os.environ)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_windows_behaviour_get_item_as_kwargs(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment(**os.environ)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"
