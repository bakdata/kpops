from enum import Enum

FILE_PREFIX = ".yaml"


class KpopsResources(str, Enum):
    PIPELINE = "pipeline"
    DEFAULT = "default"
    CONFIG = "config"

    def as_yaml_file(self, suffix: str = "", prefix: str = "") -> str:
        return suffix + self.value + prefix + FILE_PREFIX
