from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Annotated

import pydantic
from pydantic import Field, model_validator

from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
)

if TYPE_CHECKING:
    try:
        from typing import Self
    except ImportError:
        from typing import Self


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


Weight = Annotated[int, pydantic.Field(ge=1, le=100)]


class NodeSelectorOperator(str, enum.Enum):
    """Represents a key's relationship to a set of values. Valid operators are In, NotIn, Exists, DoesNotExist. Gt, and Lt."""

    IN = "In"
    NOT_IN = "NotIn"
    EXISTS = "Exists"
    DOES_NOT_EXIST = "DoesNotExist"
    GT = "Gt"
    LT = "Lt"


class NodeSelectorRequirement(DescConfigModel, CamelCaseConfigModel):
    """A node selector requirement is a selector that contains values, a key, and an operator that relates the key and values.

    :param key: The label key that the selector applies to.
    :param values: An array of string values. If the operator is In or NotIn, the values array must be non-empty. If the operator is Exists or DoesNotExist, the values array must be empty. If the operator is Gt or Lt, the values array must have a single element, which will be interpreted as an integer. This array is replaced during a strategic merge patch.
    """

    key: str = Field(description=describe_attr("key", __doc__))
    operator: NodeSelectorOperator
    values: list[str] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("values", __doc__),
    )

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        match self.operator:
            case NodeSelectorOperator.IN | NodeSelectorOperator.NOT_IN:
                assert self.values, (
                    "If the operator is In or NotIn, the values array must be non-empty."
                )
            case NodeSelectorOperator.EXISTS | NodeSelectorOperator.DOES_NOT_EXIST:
                assert not self.values, (
                    "If the operator is Exists or DoesNotExist, the values array must be empty."
                )
            case NodeSelectorOperator.GT | NodeSelectorOperator.LT:
                assert len(self.values) == 1, (
                    "If the operator is Gt or Lt, the values array must have a single element, which will be interpreted as an integer."
                )
        return self


class NodeSelectorTerm(SerializeAsOptionalModel, DescConfigModel, CamelCaseConfigModel):
    """A null or empty node selector term matches no objects. The requirements of them are ANDed. The TopologySelectorTerm type implements a subset of the NodeSelectorTerm.

    :param match_expressions: A list of node selector requirements by node's labels.
    :param match_fields: A list of node selector requirements by node's fields.
    """

    match_expressions: SerializeAsOptional[list[NodeSelectorRequirement]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("match_expressions", __doc__),
    )
    match_fields: SerializeAsOptional[list[NodeSelectorRequirement]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("match_fields", __doc__),
    )


class NodeSelector(DescConfigModel, CamelCaseConfigModel):
    """A node selector represents the union of the results of one or more label queries over a set of nodes; that is, it represents the OR of the selectors represented by the node selector terms.

    :param node_selector_terms: A list of node selector terms. The terms are ORed.
    """

    node_selector_terms: list[NodeSelectorTerm] = Field(
        description=describe_attr("node_selector_terms", __doc__)
    )


class PreferredSchedulingTerm(DescConfigModel, CamelCaseConfigModel):
    """An empty preferred scheduling term matches all objects with implicit weight 0 (i.e. it's a no-op). A null preferred scheduling term matches no objects (i.e. is also a no-op).

    :param preference: A node selector term, associated with the corresponding weight.
    :param weight: Weight associated with matching the corresponding nodeSelectorTerm, in the range 1-100.
    """

    preference: NodeSelectorTerm = Field(
        description=describe_attr("preference", __doc__)
    )
    weight: Weight = Field(description=describe_attr("weight", __doc__))


class NodeAffinity(SerializeAsOptionalModel, DescConfigModel, CamelCaseConfigModel):
    """Node affinity is a group of node affinity scheduling rules.

    :param required_during_scheduling_ignored_during_execution: If the affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to an update), the system may or may not try to eventually evict the pod from its node.
    :param preferred_during_scheduling_ignored_during_execution: The scheduler will prefer to schedule pods to nodes that satisfy the affinity expressions specified by this field, but it may choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.), compute a sum by iterating through the elements of this field and adding *weight* to the sum if the node matches the corresponding matchExpressions; the node(s) with the highest sum are the most preferred.
    """

    required_during_scheduling_ignored_during_execution: NodeSelector | None = Field(
        default=None,
        description=describe_attr(
            "required_during_scheduling_ignored_during_execution", __doc__
        ),
    )
    preferred_during_scheduling_ignored_during_execution: SerializeAsOptional[
        list[PreferredSchedulingTerm]
    ] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr(
            "preferred_during_scheduling_ignored_during_execution", __doc__
        ),
    )


class LabelSelectorOperator(str, enum.Enum):
    """Operator represents a key's relationship to a set of values. Valid operators are In, NotIn, Exists and DoesNotExist."""

    IN = "In"
    NOT_IN = "NotIn"
    EXISTS = "Exists"
    DOES_NOT_EXIST = "DoesNotExist"


class LabelSelectorRequirement(DescConfigModel, CamelCaseConfigModel):
    """A label selector requirement is a selector that contains values, a key, and an operator that relates the key and values.

    :param key: key is the label key that the selector applies to.
    :param values: An array of string values. If the operator is In or NotIn, the values array must be non-empty. If the operator is Exists or DoesNotExist, the values array must be empty. This array is replaced during a strategic merge patch.
    """

    key: str = Field(
        description=describe_attr("key", __doc__),
    )
    operator: LabelSelectorOperator
    values: list[str] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("values", __doc__),
    )

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        match self.operator:
            case LabelSelectorOperator.IN | LabelSelectorOperator.NOT_IN:
                assert self.values, (
                    "If the operator is In or NotIn, the values array must be non-empty."
                )
            case LabelSelectorOperator.EXISTS | LabelSelectorOperator.DOES_NOT_EXIST:
                assert not self.values, (
                    "If the operator is Exists or DoesNotExist, the values array must be empty."
                )
        return self


class LabelSelector(SerializeAsOptionalModel, DescConfigModel, CamelCaseConfigModel):
    """A label selector is a label query over a set of resources. The result of matchLabels and matchExpressions are ANDed. An empty label selector matches all objects. A null label selector matches no objects.

    :param match_labels: matchLabels is a map of {key,value} pairs. A single {key,value} in the matchLabels map is equivalent to an element of matchExpressions, whose key field is *key*, the operator is *In*, and the values array contains only *value*. The requirements are ANDed.
    :param match_expressions: matchExpressions is a list of label selector requirements. The requirements are ANDed.
    """

    match_labels: SerializeAsOptional[dict[str, str]] = Field(
        default={},  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("match_labels", __doc__),
    )
    match_expressions: SerializeAsOptional[list[LabelSelectorRequirement]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("match_expressions", __doc__),
    )


class PodAffinityTerm(SerializeAsOptionalModel, DescConfigModel, CamelCaseConfigModel):
    """Defines a set of pods (namely those matching the labelSelector relative to the given namespace(s)) that this pod should be co-located (affinity) or not co-located (anti-affinity) with, where co-located is defined as running on a node whose value of the label with key <topologyKey> matches that of any node on which a pod of the set of pods is running.

    :param label_selector: A label query over a set of resources, in this case pods. If it's null, this PodAffinityTerm matches with no Pods.
    :param match_label_keys: MatchLabelKeys is a set of pod label keys to select which pods will be taken into consideration. The keys are used to lookup values from the incoming pod labels, those key-value labels are merged with `labelSelector` as `key in (value)` to select the group of existing pods which pods will be taken into consideration for the incoming pod's pod (anti) affinity. Keys that don't exist in the incoming pod labels will be ignored. The default value is empty. The same key is forbidden to exist in both matchLabelKeys and labelSelector. Also, matchLabelKeys cannot be set when labelSelector isn't set. This is a beta field and requires enabling MatchLabelKeysInPodAffinity feature gate (enabled by default).
    :param mismatch_label_keys: MismatchLabelKeys is a set of pod label keys to select which pods will be taken into consideration. The keys are used to lookup values from the incoming pod labels, those key-value labels are merged with `labelSelector` as `key notin (value)` to select the group of existing pods which pods will be taken into consideration for the incoming pod's pod (anti) affinity. Keys that don't exist in the incoming pod labels will be ignored. The default value is empty. The same key is forbidden to exist in both mismatchLabelKeys and labelSelector. Also, mismatchLabelKeys cannot be set when labelSelector isn't set. This is a beta field and requires enabling MatchLabelKeysInPodAffinity feature gate (enabled by default).
    :param topology_key: This pod should be co-located (affinity) or not co-located (anti-affinity) with the pods matching the labelSelector in the specified namespaces, where co-located is defined as running on a node whose value of the label with key topologyKey matches that of any node on which any of the selected pods is running. Empty topologyKey is not allowed.
    :param: namespaces: namespaces specifies a static list of namespace names that the term applies to. The term is applied to the union of the namespaces listed in this field and the ones selected by namespaceSelector. null or empty namespaces list and null namespaceSelector means *this pod's namespace*.
    :param namespace_selector: A label query over the set of namespaces that the term applies to. The term is applied to the union of the namespaces selected by this field and the ones listed in the namespaces field. null selector and null or empty namespaces list means *this pod's namespace*. An empty selector ({}) matches all namespaces.
    """

    label_selector: LabelSelector | None = Field(
        default=None,
        description=describe_attr("label_selector", __doc__),
    )
    match_label_keys: SerializeAsOptional[list[str]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("match_label_keys", __doc__),
    )
    mismatch_label_keys: SerializeAsOptional[list[str]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("mismatch_label_keys", __doc__),
    )
    topology_key: str = Field(
        description=describe_attr("topology_key", __doc__),
    )
    namespaces: SerializeAsOptional[list[str]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr("namespaces", __doc__),
    )
    namespace_selector: LabelSelector | None = Field(
        default=None,
        description=describe_attr("namespace_selector", __doc__),
    )


class WeightedPodAffinityTerm(DescConfigModel, CamelCaseConfigModel):
    """The weights of all of the matched WeightedPodAffinityTerm fields are added per-node to find the most preferred node(s).

    :param pod_affinity_term: A pod affinity term, associated with the corresponding weight.
    :param weight: weight associated with matching the corresponding podAffinityTerm, in the range 1-100.
    """

    pod_affinity_term: PodAffinityTerm = Field(
        description=describe_attr("pod_affinity_term", __doc__),
    )
    weight: Weight = Field(
        description=describe_attr("weight", __doc__),
    )


class PodAffinity(SerializeAsOptionalModel, DescConfigModel, CamelCaseConfigModel):
    """Pod affinity is a group of inter pod affinity scheduling rules.

    :param required_during_scheduling_ignored_during_execution: If the affinity requirements specified by this field are not met at scheduling time, the pod will not be scheduled onto the node. If the affinity requirements specified by this field cease to be met at some point during pod execution (e.g. due to a pod label update), the system may or may not try to eventually evict the pod from its node. When there are multiple elements, the lists of nodes corresponding to each podAffinityTerm are intersected, i.e. all terms must be satisfied.
    :param preferred_during_scheduling_ignored_during_execution: The scheduler will prefer to schedule pods to nodes that satisfy the affinity expressions specified by this field, but it may choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.), compute a sum by iterating through the elements of this field and adding weight to the sum if the node has pods which matches the corresponding podAffinityTerm; the node(s) with the highest sum are the most preferred.
    """

    required_during_scheduling_ignored_during_execution: SerializeAsOptional[
        list[PodAffinityTerm]
    ] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr(
            "required_during_scheduling_ignored_during_execution", __doc__
        ),
    )
    preferred_during_scheduling_ignored_during_execution: SerializeAsOptional[
        list[WeightedPodAffinityTerm]
    ] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description=describe_attr(
            "preferred_during_scheduling_ignored_during_execution", __doc__
        ),
    )


class Affinity(DescConfigModel, CamelCaseConfigModel):
    """Affinity is a group of affinity scheduling rules.

    https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity

    :param node_affinity: Describes node affinity scheduling rules for the pod.
    :param pod_affinity: Describes pod affinity scheduling rules (e.g. co-locate this pod in the same node, zone, etc. as some other pod(s)).
    :param pod_anti_affinity: Describes pod anti-affinity scheduling rules (e.g. avoid putting this pod in the same node, zone, etc. as some other pod(s)).
    """

    node_affinity: NodeAffinity | None = Field(
        default=None, description=describe_attr("node_affinity", __doc__)
    )
    pod_affinity: PodAffinity | None = Field(
        default=None, description=describe_attr("pod_affinity", __doc__)
    )
    pod_anti_affinity: PodAffinity | None = Field(
        default=None, description=describe_attr("pod_anti_affinity", __doc__)
    )


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


class Toleration(DescConfigModel, CamelCaseConfigModel):
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
    str,
    pydantic.StringConstraints(pattern=r"^\d+(\.\d+)?([EPTGMk]|Ei|Pi|Ti|Gi|Mi|Ki)?$"),
]


class ResourceDefinition(DescConfigModel):
    """Model representing the `limits` or `requests` section of Kubernetes resource specifications.

    :param cpu: The amount of CPU for this container, expressed in milli CPUs (e.g., '300m').
    :param memory: The amount of memory for this container, as integer or string with valid units such as 'Mi' or 'Gi' (e.g., '2G').
    :param ephemeral_storage: The amounf of local ephemeral storage for this container, as integer or string with valid units such as 'Mi' or 'Gi' (e.g., '2G').
    """

    cpu: CPUStr | pydantic.PositiveInt | None = Field(
        default=None,
        description=describe_attr("cpu", __doc__),
    )
    memory: MemoryStr | pydantic.PositiveInt | None = Field(
        default=None,
        description=describe_attr("memory", __doc__),
    )
    ephemeral_storage: MemoryStr | pydantic.PositiveInt | None = Field(
        default=None,
        alias="ephemeral-storage",
        description=describe_attr("ephemeral_storage", __doc__),
    )


class Resources(DescConfigModel):
    """Model representing the resource specifications for a Kubernetes container.

    :param requests: The minimum resource requirements for the container.
    :param limits: The maximum resource limits for the container.
    """

    requests: ResourceDefinition | None = Field(
        default=None,
        description=describe_attr("requests", __doc__),
    )
    limits: ResourceDefinition | None = Field(
        default=None,
        description=describe_attr("limits", __doc__),
    )
