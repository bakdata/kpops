from typing import ClassVar

from kpops.component_handlers.topic import KAFKA_REST_PROXY
from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)
from kpops.core.exception import ServiceException


class KafkaRestProxyException(ServiceException):
    service: ClassVar[str] = KAFKA_REST_PROXY


class KafkaRestProxyError(KafkaRestProxyException, HttpResponseError):
    pass


class KafkaRestProxyConnectionError(KafkaRestProxyException, ServiceConnectionError):
    pass


class TopicNotFoundException(KafkaRestProxyException):
    pass


class TopicTransactionError(KafkaRestProxyException):
    pass
