from pydantic import BaseSettings, Field

class NestedSettings(BaseSettings):
    attr: str = Field("attr")

class ParentSettings(BaseSettings):

    not_nested_field: str = Field("not_nested_field")
    nested_field: NestedSettings = Field(...)
