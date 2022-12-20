from kpops.pipeline_deployer.utils.exception import RequestsException


class TopicNotFoundException(Exception):
    pass


class KafkaRestProxyError(RequestsException):
    pass
