import logging
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import pytest

from kpops.component_handlers import ComponentHandlers
from kpops.config import KpopsConfig, TopicNameConfig, set_config
from kpops.utils.environment import ENV, Environment
from kpops.utils.yaml import load_yaml_file

logger = logging.getLogger("faker")
logger.setLevel(logging.INFO)  # quiet faker locale messages


@pytest.fixture(autouse=True, scope="session")
def setup_logging() -> None:
    from kpops.utils.logging import log

    assert log


@pytest.fixture()
def mock_os_env() -> Iterator[os._Environ[str]]:
    """Clear ``os.environ``.

    :yield: ``os.environ``. Prevents the function and the mock
        context from exiting.
    """
    with mock.patch.dict(os.environ, clear=True):
        yield os.environ


@pytest.fixture()
def mock_env() -> Iterator[Environment]:
    """Clear KPOps environment.

    :yield: ``Environment``. Prevents the function and the mock
        context from exiting.
    """
    ENV.clear()
    yield ENV


@pytest.fixture()
def load_yaml_file_clear_cache() -> Iterator[None]:
    yield
    if load_yaml_file.cache is not None:
        load_yaml_file.cache.clear()


@pytest.fixture()
def custom_components() -> Iterator[None]:
    src = Path("tests/pipeline/test_components")
    dst = Path("kpops/components/test_components")
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        yield
    finally:
        shutil.rmtree(dst)


@pytest.fixture(scope="module")
def clear_kpops_config() -> Iterator[None]:
    from kpops.config import KpopsConfig

    KpopsConfig._instance = None
    yield


@pytest.fixture(scope="module")
def clear_handlers() -> Iterator[None]:
    ComponentHandlers._instance = None
    yield


@pytest.fixture(scope="module")
def pipeline_base_dir() -> Path:
    return Path()


@pytest.fixture(scope="module")
def config(pipeline_base_dir: Path) -> KpopsConfig:
    config = KpopsConfig(
        topic_name_config=TopicNameConfig(
            default_error_topic_name="${component.type}-error-topic",
            default_output_topic_name="${component.type}-output-topic",
        ),
        kafka_brokers="broker:9092",
        pipeline_base_dir=pipeline_base_dir,
    )
    set_config(config)
    return config


@pytest.fixture(scope="module")
def handlers() -> ComponentHandlers:
    return ComponentHandlers(
        schema_handler=mock.AsyncMock(),
        connector_handler=mock.AsyncMock(),
        topic_handler=mock.AsyncMock(),
    )


KUBECONFIG = """
apiVersion: v1
clusters:
- cluster: {server: 'https://localhost:9443'}
  name: test
contexts:
- context: {cluster: test, user: test}
  name: test
current-context: test
kind: Config
preferences: {}
users:
- name: test
  user: {token: testtoken}
"""


@pytest.fixture(scope="session")
def kubeconfig(tmp_path_factory: pytest.TempPathFactory) -> Path:
    kubeconfig = tmp_path_factory.mktemp("kpops") / "kubeconfig"
    kubeconfig.write_text(KUBECONFIG)
    os.environ["KUBECONFIG"] = str(kubeconfig)
    return kubeconfig
