from pathlib import Path

from pydantic import BaseModel, Field


class HelmDiffConfig(BaseModel):
    enable: bool = True
    ignore: set[str] = Field(
        default_factory=set,
        description="keypaths using dot-notation to exclude",
    )


class HelmConfig(BaseModel):
    repository_name: str
    url: str
    version: str | None = None
    context: str | None = None
    username: str | None = None
    password: str | None = None
    diff: HelmDiffConfig = HelmDiffConfig()
    namespace: str | None = None
    ca_file: Path | None = None
    insecure_skip_tls_verify: bool = False
