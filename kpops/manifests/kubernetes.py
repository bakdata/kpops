import pydantic


# TODO: use an existing library for Kubernetes models, e.g. lightkube (dataclass-based) or kubernetes-dynamic (Pydantic-based)
class ObjectMeta(pydantic.BaseModel):
    annotations: dict[str, str] | None = None
    labels: dict[str, str] | None = None
    # ...


class KubernetesManifest(pydantic.BaseModel):
    group: str
    version: str
    kind: str
    metadata: ObjectMeta
