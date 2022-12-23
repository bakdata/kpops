from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import yaml
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


HELM_SOURCE_PREFIX = "# Source: "


@dataclass
class HelmTemplate:
    filepath: str
    template: dict

    @staticmethod
    def parse_source(source: str) -> str:
        """Parse source path from comment at the beginning of the YAML doc.
        Example: # Source: chart/templates/serviceaccount.yaml
        """
        if not source.startswith(HELM_SOURCE_PREFIX):
            raise ValueError("Not a valid Helm template source")
        return source.removeprefix(HELM_SOURCE_PREFIX).strip()

    @classmethod
    def load(cls, filepath: str, content: str):
        template = yaml.load(content, yaml.Loader)
        return cls(filepath, template)


@dataclass
class YamlReader:
    content: str

    def __iter__(self) -> Iterator[str]:
        # discard all output before template documents
        index = self.content.index("---")
        self.content = self.content[index:-1]
        yield from self.content.splitlines()
        yield "---"  # add final divider to make parsing easier
