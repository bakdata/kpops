from __future__ import annotations

from enum import StrEnum

FILE_EXTENSION = ".yaml"


class KpopsFileType(StrEnum):
    """Enum representing different types of KPOps file naming conventions.

    Attributes:
        PIPELINE (str): Represents a pipeline YAML file type.
        DEFAULTS (str): Represents a defaults YAML file type.
        CONFIG (str): Represents a config YAML file type.
    """

    PIPELINE = "pipeline"
    DEFAULTS = "defaults"
    CONFIG = "config"

    def as_yaml_file(self, prefix: str = "", suffix: str = "") -> str:
        """Generate a YAML file name based on the enum value with optional prefix and suffix.

        Args:
            prefix (str): An optional prefix for the file name. Default is an empty string.
            suffix (str): An optional suffix for the file name. Default is an empty string.

        Returns:
            str: The constructed file name in the format '<prefix><value><suffix><FILE_PREFIX>'.

        Example:
            >>> KpopsFileType.PIPELINE.as_yaml_file(prefix="pre_", suffix="_suf")
            'pre_pipeline_suf.yaml'
        """
        return prefix + self.value + suffix + FILE_EXTENSION


PIPELINE_YAML = KpopsFileType.PIPELINE.as_yaml_file()
DEFAULTS_YAML = KpopsFileType.DEFAULTS.as_yaml_file()
CONFIG_YAML = KpopsFileType.CONFIG.as_yaml_file()
