import logging
import os
from collections.abc import Iterator
from unittest import mock

import pytest

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
