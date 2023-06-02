from kpops.component_handlers.utils.exception import RequestsException


class TopicNotFoundException(Exception):
    pass


class TopicTransactionError(Exception):
    pass


class KafkaRestProxyError(RequestsException):
    pass
