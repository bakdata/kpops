from typing import ClassVar

from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)
from kpops.core.exception import ServiceException


class KafkaRestProxyException(ServiceException):
    service: ClassVar[str] = "Kafka REST Proxy"


class KafkaRestProxyError(KafkaRestProxyException, HttpResponseError):
    pass


class KafkaRestProxyConnectionError(KafkaRestProxyException, ServiceConnectionError):
    pass


class TopicNotFoundException(KafkaRestProxyException):
    pass


class TopicTransactionError(KafkaRestProxyException):
    pass
