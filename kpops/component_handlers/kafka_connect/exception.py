from typing import ClassVar

from kpops.component_handlers.kafka_connect import KAFKA_CONNECT
from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)
from kpops.core.exception import ServiceException


class KafkaConnectException(ServiceException):
    service: ClassVar[str] = KAFKA_CONNECT


class KafkaConnectError(KafkaConnectException, HttpResponseError):
    pass


class KafkaConnectConnectionError(KafkaConnectException, ServiceConnectionError):
    pass


class ConnectorNotFoundException(KafkaConnectException):
    pass


class ConnectorStateException(KafkaConnectException):
    pass
