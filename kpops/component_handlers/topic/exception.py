from kpops.component_handlers.utils.exception import HttpxException


class TopicNotFoundException(Exception):
    pass


class TopicTransactionError(Exception):
    pass


class KafkaRestProxyError(HttpxException):
    pass
