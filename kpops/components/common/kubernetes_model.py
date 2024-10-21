import enum


class ServiceType(enum.Enum):
    """Represents the different Kubernetes service types.

    https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types
    """

    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"


class ProtocolSchema(enum.Enum):
    """Represents the different Kubernetes protocols.

    https://kubernetes.io/docs/reference/networking/service-protocols/
    """

    TCP = "TCP"
    UDP = "UDP"
    SCTP = "SCTP"
