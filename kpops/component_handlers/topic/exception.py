from typing import ClassVar

from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)
from kpops.exception import KpopsException


class KafkaRestProxyException(KpopsException):
    service: ClassVar[str] = "Kafka REST Proxy"


class KafkaRestProxyError(KafkaRestProxyException, HttpResponseError):
    pass


class KafkaRestProxyConnectionError(KafkaRestProxyException, ServiceConnectionError):
    pass


class TopicNotFoundException(KafkaRestProxyException):
    pass


class TopicTransactionError(KafkaRestProxyException):
    pass
