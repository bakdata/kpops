from unittest.mock import patch

from kpops.utils.environment import Environment


@patch("platform.system")
def test_normal_behaviour_get_item(system):
    system.return_value = "Linux"
    fake_environment = {"my": "fake", "environment": "here"}
    environment = Environment(fake_environment)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_get_item_as_kwargs(system):
    system.return_value = "Linux"
    fake_environment = {"my": "fake", "environment": "here"}
    environment = Environment(**fake_environment)

    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_normal_behaviour_keys_transformation(system):
    system.return_value = "Linux"
    fake_environment = {"my": "fake", "environment": "here"}
    environment = Environment(fake_environment)

    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_normal_behaviour_set_key(system):
    system.return_value = "Linux"
    fake_environment = {"my": "fake", "environment": "here"}
    environment = Environment(fake_environment)
    environment["extra"] = "key"

    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_windows_behaviour_set_key(system):
    system.return_value = "Windows"
    fake_environment = {"MY": "fake", "ENVIRONMENT": "here"}
    environment = Environment(fake_environment)
    environment["extra"] = "key"

    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys
    assert "extra" in keys
    assert environment["extra"] == "key"


@patch("platform.system")
def test_normal_behaviour_keys_transformation_kwargs(system):
    system.return_value = "Linux"
    fake_environment = {"my": "fake", "environment": "here"}
    environment = Environment(**fake_environment)

    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation(system):
    system.return_value = "Windows"
    fake_environment = {"MY": "fake", "ENVIRONMENT": "here"}
    environment = Environment(fake_environment)

    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_keys_transformation_as_kwargs(system):
    system.return_value = "Windows"
    fake_environment = {"MY": "fake", "ENVIRONMENT": "here"}
    environment = Environment(**fake_environment)
    keys = list(environment.keys())
    assert "my" in keys
    assert "environment" in keys


@patch("platform.system")
def test_windows_behaviour_get_item(system):
    system.return_value = "Windows"
    fake_environment = {"MY": "fake", "ENVIRONMENT": "here"}
    environment = Environment(fake_environment)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"


@patch("platform.system")
def test_windows_behaviour_get_item_as_kwargs(system):
    system.return_value = "Windows"
    fake_environment = {"MY": "fake", "ENVIRONMENT": "here"}
    environment = Environment(**fake_environment)
    assert environment["my"] == "fake"
    assert environment["environment"] == "here"
