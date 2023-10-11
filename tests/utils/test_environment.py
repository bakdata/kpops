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
    environment = Environment()

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_update_os_environ(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment()

    with pytest.raises(KeyError):
        environment["TEST"]
    os.environ["TEST"] = "test"
    assert "TEST" in environment
    assert environment["TEST"] == "test"
    keys = environment.keys()
    assert "TEST" in keys
    assert "test" in environment.values()
    items = dict(environment.items())
    assert items["TEST"] == "test"


@patch("platform.system")
def test_normal_behaviour_kwargs(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment(**{"kwarg1": "value1", "kwarg2": "value2"})

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"
    assert environment["kwarg1"] == "value1"
    assert environment["kwarg2"] == "value2"


@patch("platform.system")
def test_normal_behaviour_keys_transformation(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment()
    keys = set(environment.keys())

    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_normal_behaviour_set_key(system, fake_environment_linux):
    system.return_value = "Linux"
    environment = Environment()
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_windows_behaviour_get_item(system, fake_environment_windows):
    system.return_value = "Windows"

    environment = Environment()
    assert environment["MY"] == "fake"
    assert environment["ENVIRONMENT"] == "here"


@patch("platform.system")
def test_windows_behaviour_set_key(system, fake_environment_windows):
    system.return_value = "Windows"
    environment = Environment()
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "MY" in keys
    assert "ENVIRONMENT" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"
