import json
import logging
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import AnyHttpUrl, TypeAdapter
from pytest_mock import MockerFixture
from schema_registry.client.schema import AvroSchema
from schema_registry.client.utils import SchemaVersion

from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.to_section import (
    ToSection,
)
from kpops.components.common.topic import OutputTopicTypes, TopicConfig
from kpops.config import KpopsConfig, SchemaRegistryConfig
from kpops.utils.colorify import greenify, magentaify, yellowify
from tests.pipeline.test_components.components import TestSchemaProvider

log = logging.getLogger("SchemaHandler")


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


@pytest.fixture(autouse=True)
def log_warning_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.log.warning"
    )


@pytest.fixture(autouse=True)
def schema_registry_mock(mocker: MockerFixture) -> AsyncMock:
    schema_registry_mock_constructor = mocker.patch(
        "kpops.component_handlers.schema_handler.schema_handler.AsyncSchemaRegistryClient",
    )
    schema_registry_mock_constructor.return_value = AsyncMock()
    return schema_registry_mock_constructor.return_value


@pytest.fixture()
def topic_config() -> TopicConfig:
    return TopicConfig(
        type=OutputTopicTypes.OUTPUT,
        # pyright has no way of validating these aliased Pydantic fields because we're also using the allow_population_by_field_name setting
        key_schema=None,  # pyright: ignore[reportGeneralTypeIssues]
        value_schema="com.bakdata.kpops.test.SchemaHandlerTest",  # pyright: ignore[reportGeneralTypeIssues]
    )


@pytest.fixture()
def to_section(topic_config: TopicConfig) -> ToSection:
    return ToSection(topics={TopicName("topic-X"): topic_config})


@pytest.fixture()
def kpops_config() -> KpopsConfig:
    return KpopsConfig(
        kafka_brokers="broker:9092",
        schema_registry=SchemaRegistryConfig(
            enabled=True,
            url=TypeAdapter(AnyHttpUrl).validate_python("http://mock:8081"),  # pyright: ignore[reportCallIssue,reportArgumentType]
        ),
    )


def test_load_schema_handler(kpops_config: KpopsConfig):
    assert isinstance(SchemaHandler.load_schema_handler(kpops_config), SchemaHandler)

    config_disable = kpops_config.model_copy()
    config_disable.schema_registry = SchemaRegistryConfig(enabled=False)

    assert SchemaHandler.load_schema_handler(config_disable) is None


@pytest.mark.usefixtures("custom_components")
def test_should_lazy_load_schema_provider(kpops_config: KpopsConfig):
    schema_handler = SchemaHandler.load_schema_handler(kpops_config)

    assert schema_handler is not None

    schema_handler.schema_provider.provide_schema(
        "com.bakdata.kpops.test.SchemaHandlerTest", {}
    )
    schema_handler.schema_provider.provide_schema(
        "com.bakdata.kpops.test.SomeOtherSchemaClass", {}
    )

    assert isinstance(schema_handler.schema_provider, TestSchemaProvider)


def test_should_raise_value_error_if_schema_provider_class_not_found(
    kpops_config: KpopsConfig,
):
    schema_handler = SchemaHandler(kpops_config)

    with pytest.raises(
        ValueError,
        match="No schema provider found. "
        "Please implement the abstract method in "
        f"{SchemaProvider.__module__}.{SchemaProvider.__name__}.",
    ):
        schema_handler.schema_provider.provide_schema(
            "com.bakdata.kpops.test.SchemaHandlerTest", {}
        )


@pytest.mark.usefixtures("custom_components")
async def test_should_log_info_when_submit_schemas_that_not_exists_and_dry_run_true(
    to_section: ToSection,
    log_info_mock: MagicMock,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_handler = SchemaHandler(kpops_config)

    schema_registry_mock.get_versions.return_value = []

    await schema_handler.submit_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        greenify("Schema Submission: The subject topic-X-value will be submitted.")
    )
    schema_registry_mock.register.assert_not_called()


@pytest.mark.usefixtures("custom_components")
async def test_should_log_info_when_submit_schemas_that_exists_and_dry_run_true(
    topic_config: TopicConfig,
    to_section: ToSection,
    log_info_mock: MagicMock,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_handler = SchemaHandler(kpops_config)

    schema_registry_mock.get_versions.return_value = [1, 2, 3]
    schema_registry_mock.check_version.return_value = None
    schema_registry_mock.test_compatibility.return_value = True

    await schema_handler.submit_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        f"Schema Submission: compatible schema for topic-X-value with model {topic_config.value_schema}."
    )
    schema_registry_mock.register.assert_not_called()


@pytest.mark.usefixtures("custom_components")
async def test_should_raise_exception_when_submit_schema_that_exists_and_not_compatible_and_dry_run_true(
    topic_config: TopicConfig,
    to_section: ToSection,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_provider = TestSchemaProvider()
    schema_handler = SchemaHandler(kpops_config)
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"

    schema_registry_mock.get_versions.return_value = [1, 2, 3]
    schema_registry_mock.check_version.return_value = None
    schema_registry_mock.test_compatibility.return_value = False

    with pytest.raises(Exception, match="Schema is not compatible for") as exception:
        await schema_handler.submit_schemas(to_section, True)

    EXPECTED_SCHEMA = {
        "type": "record",
        "name": "KPOps.Employee",
        "fields": [
            {"name": "Name", "type": "string"},
            {"name": "Age", "type": "int"},
        ],
    }
    schema = schema_provider.provide_schema(schema_class, {})
    assert isinstance(schema, AvroSchema)
    assert schema.flat_schema == EXPECTED_SCHEMA
    assert (
        str(exception.value)
        == f"Schema is not compatible for topic-X-value and model {topic_config.value_schema}. \n {json.dumps(EXPECTED_SCHEMA, indent=4)}"
    )

    schema_registry_mock.register.assert_not_called()


@pytest.mark.usefixtures("custom_components")
async def test_should_log_debug_when_submit_schema_that_exists_and_registered_under_version_and_dry_run_true(
    topic_config: TopicConfig,
    to_section: ToSection,
    log_info_mock: MagicMock,
    log_debug_mock: MagicMock,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_provider = TestSchemaProvider()
    schema_handler = SchemaHandler(kpops_config)
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"
    schema = schema_provider.provide_schema(schema_class, {})
    registered_version = SchemaVersion(topic_config.value_schema, 1, schema, 1)

    schema_registry_mock.get_versions.return_value = [1]
    schema_registry_mock.check_version.return_value = registered_version

    await schema_handler.submit_schemas(to_section, True)

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


@pytest.mark.usefixtures("custom_components")
async def test_should_submit_non_existing_schema_when_not_dry(
    topic_config: TopicConfig,
    to_section: ToSection,
    log_info_mock: MagicMock,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_provider = TestSchemaProvider()
    schema_class = "com.bakdata.kpops.test.SchemaHandlerTest"
    schema = schema_provider.provide_schema(schema_class, {})
    schema_handler = SchemaHandler(kpops_config)

    schema_registry_mock.get_versions.return_value = []

    await schema_handler.submit_schemas(to_section, False)

    subject = "topic-X-value"
    log_info_mock.assert_called_once_with(
        f"Schema Submission: schema submitted for {subject} with model {topic_config.value_schema}."
    )

    schema_registry_mock.get_versions.assert_not_called()
    schema_registry_mock.register.assert_called_once_with(
        subject=subject, schema=schema
    )


async def test_should_log_correct_message_when_delete_schemas_and_in_dry_run(
    to_section: ToSection,
    log_info_mock: MagicMock,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_handler = SchemaHandler(kpops_config)

    schema_registry_mock.get_versions.return_value = []

    await schema_handler.delete_schemas(to_section, True)

    log_info_mock.assert_called_once_with(
        magentaify("Schema Deletion: will delete subject topic-X-value.")
    )

    schema_registry_mock.delete_subject.assert_not_called()


async def test_should_delete_schemas_when_not_in_dry_run(
    to_section: ToSection,
    schema_registry_mock: AsyncMock,
    kpops_config: KpopsConfig,
):
    schema_handler = SchemaHandler(kpops_config)

    schema_registry_mock.get_versions.return_value = []

    await schema_handler.delete_schemas(to_section, False)

    schema_registry_mock.delete_subject.assert_called_once_with("topic-X-value")


def test_should_log_warning_if_schema_handler_is_not_enabled_but_url_is_set(
    log_warning_mock: MagicMock,
    kpops_config: KpopsConfig,
):
    kpops_config.schema_registry.enabled = False
    SchemaHandler.load_schema_handler(kpops_config)

    log_warning_mock.assert_called_once_with(
        yellowify(
            f"The property schema_registry.enabled is set to False but the URL is set to {kpops_config.schema_registry.url}."
            f"\nIf you want to use the schema handler make sure to enable it."
        )
    )
