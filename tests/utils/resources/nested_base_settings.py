from pydantic import Field
from pydantic_settings import BaseSettings


class NestedSettings(BaseSettings):
    attr: str = Field("attr")


class ParentSettings(BaseSettings):
    not_nested_field: str = Field("not_nested_field")
    nested_field: NestedSettings = Field(...)
    field_with_env_defined: str = Field(
        alias="FIELD_WITH_ENV_DEFINED",
    )
