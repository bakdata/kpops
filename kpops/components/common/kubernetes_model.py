import enum

from pydantic import BaseModel, Field


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


class ImagePullPolicy(enum.Enum):
    """Represents the different Kubernetes image pull policies."""

    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class ResourceLimits(BaseModel):
    cpu: str = Field(pattern=r"^\d+m$")
    memory: str = Field(pattern=r"^\d+[KMGi]+$")


class ResourceRequests(BaseModel):
    cpu: str = Field(pattern=r"^\d+m$")
    memory: str = Field(pattern=r"^\d+[KMGi]+$")


class Resources(BaseModel):
    requests: ResourceRequests
    limits: ResourceLimits
