import enum

from pydantic import BaseModel, Field

from kpops.utils.docstring import describe_attr


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
    """Model representing the 'limits' section of Kubernetes resource specifications.

    :param cpu: The maximum amount of CPU a container can use, expressed in milli CPUs (e.g., '300m').
    :param memory: The maximum amount of memory a container can use, with valid units such as 'Mi' or 'Gi' (e.g., '2G').
    """

    cpu: str = Field(pattern=r"^\d+m$", description=describe_attr("cpu", __doc__))
    memory: str = Field(
        pattern=r"^\d+[KMGi]+$", description=describe_attr("memory", __doc__)
    )


class ResourceRequests(BaseModel):
    """Model representing the 'requests' section of Kubernetes resource specifications.

    :param cpu: The minimum amount of CPU requested for the container, expressed in milli CPUs (e.g., '100m').
    :param memory: The minimum amount of memory requested for the container, with valid units such as 'Mi' or 'Gi' (e.g., '500Mi').
    """

    cpu: str = Field(pattern=r"^\d+m$", description=describe_attr("cpu", __doc__))
    memory: str = Field(
        pattern=r"^\d+[KMGi]+$", description=describe_attr("memory", __doc__)
    )


class Resources(BaseModel):
    """Model representing the resource specifications for a Kubernetes container.

    :param requests: The minimum resource requirements for the container.
    :param limits: The maximum resource limits for the container.
    """

    requests: ResourceRequests = Field(description=describe_attr("requests", __doc__))
    limits: ResourceLimits = Field(description=describe_attr("limits", __doc__))


class RestartPolicy(enum.Enum):
    ALWAYS = "Always"
    ON_FAILURE = "OnFailure"
    NEVER = "Never"
