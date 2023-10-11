import os
from unittest.mock import ANY

import pytest

from kpops.utils.environment import Environment


@pytest.fixture(autouse=True)
def environment(monkeypatch: pytest.MonkeyPatch) -> Environment:
    for key in os.environ:
        monkeypatch.delenv(key)
    monkeypatch.setenv("MY", "fake")
    monkeypatch.setenv("ENVIRONMENT", "here")
    return Environment()


def test_get_item(environment: Environment):
    assert environment["MY"] == "fake"
    assert environment["ENVIRONMENT"] == "here"


def test_set_item(environment: Environment):
    environment["extra"] = "key"

    keys = set(environment.keys())
    assert "MY" in keys
    assert "ENVIRONMENT" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


def test_update_os_environ(environment: Environment):
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


def test_mapping():
    environment = Environment(**{"kwarg1": "value1", "kwarg2": "value2"})
    assert environment["MY"] == "fake"
    assert environment["ENVIRONMENT"] == "here"
    assert environment["kwarg1"] == "value1"
    assert environment["kwarg2"] == "value2"


def test_kwargs():
    environment = Environment(kwarg1="value1", kwarg2="value2")
    assert environment["MY"] == "fake"
    assert environment["ENVIRONMENT"] == "here"
    assert environment["kwarg1"] == "value1"
    assert environment["kwarg2"] == "value2"


def test_dict(environment: Environment):
    assert environment.dict == {
        "MY": "fake",
        "ENVIRONMENT": "here",
        "PYTEST_CURRENT_TEST": ANY,
    }
