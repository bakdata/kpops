from pathlib import Path

import pytest

from kpops.component_handlers import ComponentHandlers
from kpops.config import KpopsConfig
from tests.components import PIPELINE_BASE_DIR


@pytest.fixture(scope="module")
def pipeline_base_dir() -> Path:
    return PIPELINE_BASE_DIR


@pytest.fixture(autouse=True, scope="module")
def _apply_config_and_handlers(
    config: KpopsConfig, handlers: ComponentHandlers
) -> None:
    pass
