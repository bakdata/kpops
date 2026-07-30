from typing import ClassVar

from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)
from kpops.exception import ServiceException


class KafkaConnectException(ServiceException):
    service: ClassVar[str] = "Kafka Connect"


class KafkaConnectError(KafkaConnectException, HttpResponseError):
    pass


class KafkaConnectConnectionError(KafkaConnectException, ServiceConnectionError):
    pass


class ConnectorNotFoundException(KafkaConnectException):
    pass


class ConnectorStateException(KafkaConnectException):
    pass
