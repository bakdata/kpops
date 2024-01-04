from pathlib import Path

from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmFlags
from kpops.components.base_components.kafka_app import StreamsBootstrap


class RcloneCopy(StreamsBootstrap):
    rclone_conf_path: Path

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/rclone-copy"

    @property
    @override
    def helm_flags(self) -> HelmFlags:
        flags = super().helm_flags
        flags.set_file = {"rcloneConf": self.rclone_conf_path}
        return flags
