from pydantic import BaseModel, Field, model_validator
from typing_extensions import Any


class StrimziSpecSection(BaseModel):
    partitions: int = Field(default=1)
    replicas: int = Field(default=1)
    config: dict[str, str | int] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def set_defaults_if_none(cls, values: Any) -> Any:
        if values.get("partitions") is None:
            values["partitions"] = 1
        if values.get("replicas") is None:
            values["replicas"] = 1
        return values


class StrimziTopic(BaseModel):
    name: str
    spec: StrimziSpecSection = Field(default=None)
