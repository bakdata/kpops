import enum
from typing import Annotated

import pydantic
from pydantic import Field

from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfigModel


class ServiceType(str, enum.Enum):
    """Represents the different Kubernetes service types.

    https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types
    """

    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"


class ProtocolSchema(str, enum.Enum):
    """Represents the different Kubernetes protocols.

    https://kubernetes.io/docs/reference/networking/service-protocols/
    """

    TCP = "TCP"
    UDP = "UDP"
    SCTP = "SCTP"


class ImagePullPolicy(str, enum.Enum):
    """Represents the different Kubernetes image pull policies.

    https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy
    """

    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class Operation(str, enum.Enum):
    EXISTS = "Exists"
    EQUAL = "Equal"


class Effects(str, enum.Enum):
    NO_EXECUTE = "NoExecute"
    NO_SCHEDULE = "NoSchedule"
    PREFER_NO_SCHEDULE = "PreferNoSchedule"


class RestartPolicy(str, enum.Enum):
    ALWAYS = "Always"
    ON_FAILURE = "OnFailure"
    NEVER = "Never"


class Toleration(DescConfigModel):
    """Represents the different Kubernetes tolerations.

    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

    :param key: The key that the toleration applies to.
    :param operator: The operator ('Exists' or 'Equal').
    :param value: The value to match for the key.
    :param effect: The effect to tolerate.
    :param toleration_seconds: The duration for which the toleration is valid.
    """

    key: str = Field(description=describe_attr("key", __doc__))

    operator: Operation = Field(description=describe_attr("operator", __doc__))

    effect: Effects = Field(description=describe_attr("effect", __doc__))

    value: str | None = Field(default=None, description=describe_attr("value", __doc__))

    toleration_seconds: int | None = Field(
        default=None, description=describe_attr("toleration_seconds", __doc__)
    )


CPUStr = Annotated[str, pydantic.StringConstraints(pattern=r"^\d+m$")]
MemoryStr = Annotated[
    # Matches plain number string or number with valid suffixes: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
    str, pydantic.StringConstraints(pattern=r"^\d+([EPTGMk]|Ei|Pi|Ti|Gi|Mi|Ki)?$")
]


class ResourceDefinition(DescConfigModel):
    """Model representing the `limits` or `requests` section of Kubernetes resource specifications.

    :param cpu: The maximum amount of CPU a container can use, expressed in milli CPUs (e.g., '300m').
    :param memory: The maximum amount of memory a container can use, as integer or string with valid units such as 'Mi' or 'Gi' (e.g., '2G').
    """

    cpu: CPUStr | pydantic.PositiveInt | None = Field(
        default=None,
        description=describe_attr("cpu", __doc__),
    )
    memory: MemoryStr | pydantic.PositiveInt | None = Field(
        default=None,
        description=describe_attr("memory", __doc__),
    )


class Resources(DescConfigModel):
    """Model representing the resource specifications for a Kubernetes container.

    :param requests: The minimum resource requirements for the container.
    :param limits: The maximum resource limits for the container.
    """

    requests: ResourceDefinition = Field(description=describe_attr("requests", __doc__))
    limits: ResourceDefinition = Field(description=describe_attr("limits", __doc__))
