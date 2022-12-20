from kpops.pipeline_deployer.utils.exception import RequestsException


class ConnectorNotFoundException(Exception):
    pass


class KafkaConnectError(RequestsException):
    pass
