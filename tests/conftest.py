import logging
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import pytest

from kpops.config import KpopsConfig
from kpops.utils.environment import ENV, Environment
from kpops.utils.yaml import load_yaml_file

logger = logging.getLogger("faker")
logger.setLevel(logging.INFO)  # quiet faker locale messages


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
    load_yaml_file.cache.clear()  # pyright: ignore[reportFunctionMemberAccess]


@pytest.fixture()
def custom_components():
    src = Path("tests/pipeline/test_components")
    dst = Path("kpops/components/test_components")
    try:
        shutil.copytree(src, dst)
        yield
    finally:
        shutil.rmtree(dst)


@pytest.fixture(scope="module")
def clear_kpops_config():
    yield
    KpopsConfig._instance = None
