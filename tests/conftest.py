import os
from collections.abc import Iterator
from unittest import mock

import pytest

from kpops.utils.yaml_loading import load_yaml_file


@pytest.fixture()
def mock_env() -> Iterator[os._Environ[str]]:
    """Clear ``os.environ``.

    :yield: ``os.environ``. Prevents the function and the mock
        context from exiting.
    """
    with mock.patch.dict(os.environ, clear=True):
        yield os.environ


@pytest.fixture()
def load_yaml_file_clear_cache() -> Iterator[None]:
    yield
    load_yaml_file.cache.clear()
