from kpops.component_handlers.utils.exception import HttpxException


class ConnectorNotFoundException(Exception):
    pass


class ConnectorStateException(Exception):
    pass


class KafkaConnectError(HttpxException):
    pass
