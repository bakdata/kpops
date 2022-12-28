from kpops.component_handlers.utils.exception import RequestsException


class ConnectorNotFoundException(Exception):
    pass


class KafkaConnectError(RequestsException):
    pass
