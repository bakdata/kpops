import json
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from schema_registry.client.utils import SchemaVersion

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.utils.colorify import greenify, magentaify
from tests.cli.test_registry import SubComponent
from tests.component_handlers.schema_handler.resources.module import (
    CustomSchemaProvider,
)
from tests.pipeline.test_components import TestSchemaProvider

NON_EXISTING_PROVIDER_MODULE = SubComponent.__module__
SCHEMA_PROVIDER_MODULE = CustomSchemaProvider.__module__
TEST_SCHEMA_PROVIDER_MODULE = TestSchemaProvider.__module__


@pytest.fixture(autouse=True)
def log_info_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.log.info"
    )


@pytest.fixture(autouse=True)
def log_debug_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.log.debug"
    )


@pytest.fixture(autouse=False)
def find_class_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.find_class"
    )


@pytest.fixture(autouse=True)
def schema_registry_mock(mocker: MockerFixture) -> MagicMock:
    schema_registry_mock = mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.SchemaRegistryClient"
    )
    return schema_registry_mock.return_value


def test_load_schema_handler():
    config_enable = PipelineConfig(
        defaults_path=Path("fake"),
        environment="development",
        schema_registry_url="http://localhost:8081",
    )

    config_disable = config_enable.copy()
    config_disable.schema_registry_url = None
    assert (
        SchemaHandler.load_schema_handler(TEST_SCHEMA_PROVIDER_MODULE, config_disable)
        is None
    )

    assert (
        type(
            SchemaHandler.load_schema_handler(
                TEST_SCHEMA_PROVIDER_MODULE, config_enable
            )
        )
        is SchemaHandler
    )


def test_should_lazy_load_schema_provider(find_class_mock: MagicMock):
    config_enable = PipelineConfig(
        defaults_path=Path("fake"),
        environment="development",
        schema_registry_url="http://localhost:8081",
    )
    schema_handler = SchemaHandler.load_schema_handler(
        TEST_SCHEMA_PROVIDER_MODULE, config_enable
    )

    assert schema_handler is not None

    schema_handler.schema_provider.provide_schema(
        "com.bakdata.kpops.test.SchemaHandlerTest", {}
    )
    schema_handler.schema_provider.provide_schema(
        "com.bakdata.kpops.test.SomeOtherSchemaClass", {}
    )

    find_class_mock.assert_called_once_with(TEST_SCHEMA_PROVIDER_MODULE, SchemaProvider)


def test_should_raise_value_error_if_schema_provider_class_not_found():
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=NON_EXISTING_PROVIDER_MODULE
    )

    with pytest.raises(ValueError) as value_error:
        schema_handler.schema_provider.provide_schema(
            "com.bakdata.kpops.test.SchemaHandlerTest", {}
        )

    assert (
        str(value_error.value)
        == "No schema provider found in components module tests.cli.test_registry. "
        "Please implement the abstract method in "
        f"{SchemaProvider.__module__}.{SchemaProvider.__name__}."
    )


def test_should_raise_value_error_when_schema_provider_is_called_and_components_module_is_empty():
    config_enable = PipelineConfig(
        defaults_path=Path("fake"),
        environment="development",
        schema_registry_url="http://localhost:8081",
    )

    with pytest.raises(ValueError):
        schema_handler = SchemaHandler.load_schema_handler(None, config_enable)
        assert schema_handler is not None
        schema_handler.schema_provider.provide_schema(
            "com.bakdata.kpops.test.SchemaHandlerTest", {}
        )

    with pytest.raises(ValueError) as value_error:
        schema_handler = SchemaHandler.load_schema_handler("", config_enable)
        assert schema_handler is not None
        schema_handler.schema_provider.provide_schema(
            "com.bakdata.kpops.test.SchemaHandlerTest", {}
        )

    assert (
        str(value_error.value)
        == "The Schema Registry URL is set but you haven't specified the component module path. Please provide a valid component module path where your SchemaProvider implementation exists."
    )


def test_should_log_info_when_submit_schemas_that_not_exists_and_dry_run_true(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema="com.bakdata.kpops.test.SchemaHandlerTest",
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = []

    schema_handler.submit_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        greenify("Schema Submission: The subject topic-X-value will be submitted.")
    )
    schema_registry_mock.register.assert_not_called()


def test_should_log_info_when_submit_schemas_that_exists_and_dry_run_true(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema="com.bakdata.kpops.test.SchemaHandlerTest",
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = [1, 2, 3]
    schema_registry_mock.check_version.return_value = None
    schema_registry_mock.test_compatibility.return_value = True

    schema_handler.submit_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        f"Schema Submission: compatible schema for topic-X-value with model {topic_config.value_schema}."
    )
    schema_registry_mock.register.assert_not_called()


def test_should_raise_exception_when_submit_schema_that_exists_and_not_compatible_and_dry_run_true(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_provider = TestSchemaProvider()
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema=schema_class,
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = [1, 2, 3]
    schema_registry_mock.check_version.return_value = None
    schema_registry_mock.test_compatibility.return_value = False

    with pytest.raises(Exception) as exception:
        schema_handler.submit_schemas(to_section, True)

    schema = schema_provider.provide_schema(schema_class, {})
    assert (
        str(exception.value)
        == f"Schema is not compatible for topic-X-value and model {topic_config.value_schema}. \n {json.dumps(schema.flat_schema, indent=4)}"
    )

    schema_registry_mock.register.assert_not_called()


def test_should_log_debug_when_submit_schema_that_exists_and_registered_under_version_and_dry_run_true(
    log_info_mock: MagicMock, log_debug_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_provider = TestSchemaProvider()
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema=schema_class,
    )
    to_section = ToSection(topics={"topic-X": topic_config})
    schema = schema_provider.provide_schema(schema_class, {})
    registered_version = SchemaVersion(topic_config.value_schema, 1, schema, 1)

    schema_registry_mock.get_versions.return_value = [1]
    schema_registry_mock.check_version.return_value = registered_version

    schema_handler.submit_schemas(to_section, True)

    assert log_info_mock.mock_calls == [
        mock.call(
            f"Schema Submission: compatible schema for topic-X-value with model {topic_config.value_schema}."
        ),
    ]

    assert log_debug_mock.mock_calls == [
        mock.call(
            f"Schema Submission: schema was already submitted for the subject topic-X-value as version {registered_version.schema}. Therefore, the specified schema must be compatible."
        ),
    ]

    schema_registry_mock.register.assert_not_called()


def test_should_submit_non_existing_schema_when_not_dry(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_provider = TestSchemaProvider()
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"
    schema = schema_provider.provide_schema(schema_class, {})
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema=schema_class,
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = []

    schema_handler.submit_schemas(to_section, False)

    subject = "topic-X-value"
    log_info_mock.assert_called_once_with(
        f"Schema Submission: schema submitted for {subject} with model {topic_config.value_schema}."
    )

    schema_registry_mock.get_versions.assert_not_called()
    schema_registry_mock.register.assert_called_once_with(
        subject=subject, schema=schema
    )


def test_should_log_correct_message_when_delete_schemas_and_in_dry_run(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema="com.bakdata.kpops.test.SchemaHandlerTest",
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = []

    schema_handler.delete_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        magentaify("Schema Deletion: will delete subject topic-X-value.")
    )

    schema_registry_mock.delete_subject.assert_not_called()


def test_should_delete_schemas_when_not_in_dry_run(
    log_info_mock: MagicMock, schema_registry_mock: MagicMock
):
    schema_handler = SchemaHandler(
        url="http://mock:8081", components_module=TEST_SCHEMA_PROVIDER_MODULE
    )
    topic_config = TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        key_schema=None,
        value_schema="com.bakdata.kpops.test.SchemaHandlerTest",
    )
    to_section = ToSection(topics={"topic-X": topic_config})

    schema_registry_mock.get_versions.return_value = []

    schema_handler.delete_schemas(to_section, False)

    schema_registry_mock.delete_subject.assert_called_once_with("topic-X-value")
