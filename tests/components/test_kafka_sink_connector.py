from unittest.mock import ANY, MagicMock, call

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from kpops.component_handlers import get_handlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.component_handlers.kafka_connect.model import (
    ConnectorNewState,
    KafkaConnectorConfig,
    KafkaConnectorType,
)
from kpops.components.base_components.kafka_connector import (
    KafkaConnectorResetter,
    KafkaSinkConnector,
)
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    ToSection,
)
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.utils.colorify import magentaify
from tests.components.test_kafka_connector import (
    CONNECTOR_CLEAN_FULL_NAME,
    CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
    CONNECTOR_CLEAN_RELEASE_NAME,
    CONNECTOR_FULL_NAME,
    CONNECTOR_NAME,
    RESETTER_NAMESPACE,
    TestKafkaConnector,
)

CONNECTOR_TYPE = KafkaConnectorType.SINK.value


class TestKafkaSinkConnector(TestKafkaConnector):
    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kafka_connector.log.info")

    @override
    @pytest.fixture()
    def connector(self, connector_config: KafkaConnectorConfig) -> KafkaSinkConnector:
        return KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            to=ToSection(
                topics={
                    TopicName("${output_topic_name}"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

    def test_resetter(self, connector: KafkaSinkConnector):
        resetter = connector._resetter
        assert isinstance(resetter, KafkaConnectorResetter)
        assert resetter.full_name == CONNECTOR_CLEAN_FULL_NAME

    def test_resetter_release_name(self, connector: KafkaSinkConnector):
        assert connector.config.name == CONNECTOR_FULL_NAME
        assert connector._resetter.helm_release_name == CONNECTOR_CLEAN_RELEASE_NAME

    def test_resetter_helm_name_override(self, connector: KafkaSinkConnector):
        assert (
            connector._resetter.to_helm_values()["nameOverride"]
            == CONNECTOR_CLEAN_HELM_NAMEOVERRIDE
        )
        assert (
            connector._resetter.to_helm_values()["fullnameOverride"]
            == CONNECTOR_CLEAN_HELM_NAMEOVERRIDE
        )

    def test_resetter_inheritance(self, connector: KafkaSinkConnector):
        setattr(connector.resetter_values, "testKey", "foo")
        resetter = connector._resetter
        assert resetter
        assert not hasattr(resetter, "_resetter")

        assert not hasattr(resetter, "resetter_namespace")
        assert resetter.namespace == connector.resetter_namespace

        assert not hasattr(resetter, "resetter_values")
        # check that resetter values are contained in resetter app values
        assert (
            connector.resetter_values.model_dump().items()
            <= resetter.values.model_dump().items()
        )

    def test_connector_config_parsing(self, connector_config: KafkaConnectorConfig):
        topic_pattern = ".*"
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=KafkaConnectorConfig.model_validate(
                {
                    **connector_config.model_dump(),
                    "topics.regex": topic_pattern,
                }
            ),
            resetter_namespace=RESETTER_NAMESPACE,
        )
        assert connector.config.topics_regex == topic_pattern
        assert connector.config.model_dump()["topics.regex"] == topic_pattern

    def test_from_section_parsing_input_topic(
        self, connector_config: KafkaConnectorConfig
    ):
        topic1 = TopicName("connector-topic1")
        topic2 = TopicName("connector-topic2")
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            from_=FromSection(
                topics={
                    topic1: FromTopic(type=InputTopicTypes.INPUT),
                    topic2: FromTopic(type=InputTopicTypes.INPUT),
                }
            ),
        )
        assert connector.config.topics == [
            KafkaTopic(name=topic1),
            KafkaTopic(name=topic2),
        ]

        topic3 = "connector-topic3"
        connector.add_input_topics(
            [
                KafkaTopic(name=topic1),
                KafkaTopic(name=topic3),
            ]
        )
        assert connector.config.topics == [
            KafkaTopic(name=topic1),
            KafkaTopic(name=topic2),
            KafkaTopic(name=topic3),
        ]

        assert connector.config.model_dump()["topics"] == f"{topic1},{topic2},{topic3}"

    def test_from_section_parsing_input_pattern(
        self, connector_config: KafkaConnectorConfig
    ):
        topic_pattern = TopicName(".*")
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            from_=FromSection(
                topics={topic_pattern: FromTopic(type=InputTopicTypes.PATTERN)}
            ),
        )
        assert connector.config.topics_regex == topic_pattern

    async def test_deploy_order(
        self,
        connector: KafkaSinkConnector,
        mocker: MockerFixture,
    ):
        mock_create_topic = mocker.patch.object(
            get_handlers().topic_handler, "create_topic"
        )
        mock_create_connector = mocker.patch.object(
            get_handlers().connector_handler, "create_connector"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock.attach_mock(mock_create_connector, "mock_create_connector")
        dry_run = True

        await connector.deploy(dry_run=dry_run)
        assert connector.to
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=dry_run)
                for topic in connector.to.kafka_topics
            ),
            mocker.call.mock_create_connector(
                connector.config, state=None, dry_run=dry_run
            ),
        ]

    @pytest.mark.parametrize(
        "initial_state",
        [None, ConnectorNewState.RUNNING, ConnectorNewState.PAUSED],
    )
    async def test_deploy_initial_state(
        self,
        connector: KafkaSinkConnector,
        initial_state: ConnectorNewState | None,
        mocker: MockerFixture,
    ):
        mock_create_connector = mocker.patch.object(
            get_handlers().connector_handler, "create_connector"
        )

        connector.state = initial_state
        dry_run = True
        await connector.deploy(dry_run=dry_run)
        assert mock_create_connector.mock_calls == [
            mocker.call(connector.config, state=initial_state, dry_run=dry_run)
        ]

    async def test_destroy(
        self,
        connector: KafkaSinkConnector,
        mocker: MockerFixture,
    ):
        mock_destroy_connector = mocker.patch.object(
            get_handlers().connector_handler, "destroy_connector"
        )

        await connector.destroy(dry_run=True)

        mock_destroy_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=True
        )

    async def test_reset_when_dry_run_is_true(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_resetter_reset = mocker.spy(connector._resetter, "reset")
        dry_run = True
        await connector.reset(dry_run=dry_run)

        mock_destroy.assert_called_once_with(dry_run)
        mock_resetter_reset.assert_called_once_with(dry_run)
        dry_run_handler_mock.print_helm_diff.assert_called_once()

    async def test_reset_when_dry_run_is_false(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_clean_connector = mocker.patch.object(
            get_handlers().connector_handler, "clean_connector"
        )
        mock_resetter_reset = mocker.spy(connector._resetter, "reset")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_destroy, "destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False

        await connector.reset(dry_run=dry_run)
        mock_resetter_reset.assert_called_once_with(dry_run)

        mock.assert_has_calls(
            [
                mocker.call.destroy_connector(dry_run),
                mocker.call.helm.add_repo(
                    "bakdata-kafka-connect-resetter",
                    "https://bakdata.github.io/kafka-connect-resetter/",
                    RepoAuthFlags(),
                ),
                mocker.call.helm.uninstall(
                    RESETTER_NAMESPACE,
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
                ANY,  # __bool__
                ANY,  # __str__
                mocker.call.helm.upgrade_install(
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                    dry_run,
                    RESETTER_NAMESPACE,
                    {
                        "nameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                        "fullnameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                        "connectorType": CONNECTOR_TYPE,
                        "config": {
                            "brokers": "broker:9092",
                            "connector": CONNECTOR_FULL_NAME,
                            "deleteConsumerGroup": False,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="1.0.4",
                        wait=True,
                        wait_for_jobs=True,
                    ),
                ),
                mocker.call.helm.uninstall(
                    RESETTER_NAMESPACE,
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
                ANY,  # __bool__
                ANY,  # __str__
            ]
        )

        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_delete_topic.assert_not_called()

    async def test_clean_when_dry_run_is_true(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
    ):
        dry_run = True

        await connector.clean(dry_run=dry_run)
        dry_run_handler_mock.print_helm_diff.assert_called_once()

    async def test_clean_when_dry_run_is_false(
        self,
        connector: KafkaSinkConnector,
        helm_mock: MagicMock,
        log_info_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_destroy = mocker.patch.object(connector, "destroy")

        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_clean_connector = mocker.patch.object(
            get_handlers().connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_destroy, "destroy_connector")
        mock.attach_mock(mock_delete_topic, "mock_delete_topic")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        await connector.clean(dry_run=dry_run)

        assert log_info_mock.mock_calls == [
            call.log_info(
                magentaify(
                    f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {CONNECTOR_FULL_NAME}"
                )
            ),
            call.log_info(
                magentaify(
                    f"Connector Cleanup: deploy Connect {KafkaConnectorType.SINK.value} resetter for {CONNECTOR_FULL_NAME}"
                )
            ),
            call.log_info(magentaify("Connector Cleanup: uninstall Kafka Resetter.")),
        ]

        assert connector.to
        assert mock.mock_calls == [
            mocker.call.destroy_connector(dry_run),
            *(
                mocker.call.mock_delete_topic(topic, dry_run=dry_run)
                for topic in connector.to.kafka_topics
            ),
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                RESETTER_NAMESPACE,
                {
                    "nameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                    "fullnameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                    "connectorType": CONNECTOR_TYPE,
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "deleteConsumerGroup": True,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_without_to_when_dry_run_is_true(
        self,
        dry_run_handler_mock: MagicMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
        )

        dry_run = True

        await connector.clean(dry_run)
        dry_run_handler_mock.print_helm_diff.assert_called_once()

    async def test_clean_without_to_when_dry_run_is_false(
        self,
        helm_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
        )

        mock_destroy = mocker.patch.object(connector, "destroy")

        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_clean_connector = mocker.patch.object(
            get_handlers().connector_handler, "clean_connector"
        )
        mock = mocker.MagicMock()
        mock.attach_mock(mock_destroy, "destroy_connector")
        mock.attach_mock(mock_delete_topic, "mock_delete_topic")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        await connector.clean(dry_run)

        assert mock.mock_calls == [
            mocker.call.destroy_connector(dry_run),
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(
                    username=None,
                    password=None,
                    ca_file=None,
                    insecure_skip_tls_verify=False,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                RESETTER_NAMESPACE,
                {
                    "nameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                    "fullnameOverride": CONNECTOR_CLEAN_HELM_NAMEOVERRIDE,
                    "connectorType": CONNECTOR_TYPE,
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "deleteConsumerGroup": True,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_delete_topic.assert_not_called()
